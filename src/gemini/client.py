"""
Gemini API client integration using google-genai SDK.
Handles:
- System instruction loading and profile/mode interpolation
- Per-user memory (last 20 messages)
- Function calling (add_task, list_tasks, complete_task, calc_margin)
- Google Search grounding (in /mentor or on price/trend queries)
- Audio (.ogg) and Photo (image/jpeg) parts
- Retry with exponential backoff on 429/503
- 60s timeout handling
"""

import asyncio
import os
import re
from typing import List, Dict, Any, Optional, Union
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.config import config
from src.db.profiles import format_profile_for_prompt
from src.gemini.tools import GEMINI_FUNCTION_DECLARATIONS, execute_tool_call
from src.utils.logger import logger


class GeminiService:
    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._raw_system_prompt: str = ""
        self._load_system_prompt()

    def _load_system_prompt(self) -> None:
        """Loads system prompt template from prompts/system.md."""
        if config.SYSTEM_PROMPT_PATH.exists():
            with open(config.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                self._raw_system_prompt = f.read()
        else:
            self._raw_system_prompt = (
                'You are "Biznes Sherik" — a personal business assistant for a small business owner in Karakalpakstan / Uzbekistan.\n'
                "<profile>\n{profile}\n</profile>\n<mode>\n{mode}\n</mode>"
            )

    @property
    def client(self) -> genai.Client:
        """Lazy-loaded Google GenAI client."""
        if self._client is None:
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set.")
            self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        return self._client

    def build_system_instruction(self, profile: Optional[Dict[str, Any]], mode: str = "general") -> str:
        """Injects business profile and mode into system prompt."""
        formatted_profile = format_profile_for_prompt(profile)
        # Safe format or replace
        prompt = self._raw_system_prompt
        prompt = prompt.replace("{profile}", formatted_profile)
        prompt = prompt.replace("{mode}", mode)
        return prompt

    def should_enable_search(self, mode: str, user_text: str) -> bool:
        """
        Determines whether Google Search Grounding should be enabled:
        - Enabled in /mentor mode
        - Enabled when user asks about market prices, competitors, or industry trends.
        """
        if mode == "mentor":
            return True

        keywords = [
            "baha", "narx", "baho", "cena", "цена",
            "trend", "trendlar", "тренд", "тренда",
            "raqobatchi", "konkurent", "konkurentlar", "конкурент",
            "bozor", "bazar", "рынок", "rınok"
        ]
        text_lower = user_text.lower()
        return any(kw in text_lower for kw in keywords)

    async def generate_response(
        self,
        user_id: int,
        prompt_parts: Union[str, List[Any]],
        profile: Optional[Dict[str, Any]],
        mode: str = "general",
        history: Optional[List[Dict[str, Any]]] = None,
        scheduler_callback=None
    ) -> str:
        """
        Sends request to Gemini model with:
        - System instruction (with profile & mode)
        - Last 20 messages memory
        - Function calling tools
        - Optional Google Search grounding
        - Exponential backoff retry on 429/503
        - 60s timeout
        """
        system_instruction = self.build_system_instruction(profile, mode)

        # Build contents list
        contents: List[types.Content] = []

        # 1. Add chat history
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

        # 2. Add current user prompt (text, audio, image)
        current_parts: List[types.Part] = []
        user_text_for_search = ""
        if isinstance(prompt_parts, str):
            current_parts.append(types.Part.from_text(text=prompt_parts))
            user_text_for_search = prompt_parts
        elif isinstance(prompt_parts, list):
            for part in prompt_parts:
                if isinstance(part, str):
                    current_parts.append(types.Part.from_text(text=part))
                    user_text_for_search += " " + part
                elif isinstance(part, types.Part):
                    current_parts.append(part)
        else:
            current_parts.append(types.Part.from_text(text=str(prompt_parts)))

        contents.append(types.Content(role="user", parts=current_parts))

        # Check search grounding requirement
        enable_search = self.should_enable_search(mode, user_text_for_search)

        # Construct Tools
        tools: List[types.Tool] = []
        # Function declarations
        tools.append(types.Tool(function_declarations=GEMINI_FUNCTION_DECLARATIONS))
        if enable_search:
            try:
                tools.append(types.Tool(google_search=types.GoogleSearch()))
            except Exception as e:
                logger.warning(f"Could not attach GoogleSearch tool: {e}")

        # Config
        config_obj = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.7,
        )

        # Execute with retry & timeout
        return await self._call_with_retry_and_timeout(
            user_id=user_id,
            contents=contents,
            config_obj=config_obj,
            scheduler_callback=scheduler_callback,
            model_name=config.GEMINI_MODEL
        )

    async def _call_with_retry_and_timeout(
        self,
        user_id: int,
        contents: List[types.Content],
        config_obj: types.GenerateContentConfig,
        scheduler_callback=None,
        max_retries: int = 3,
        model_name: Optional[str] = None
    ) -> str:
        """Executes Gemini generate_content with backoff, model fallback, and function-call resolution."""
        current_model = model_name or config.GEMINI_MODEL

        for attempt in range(1, max_retries + 1):
            try:
                # Wrap inside timeout
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.models.generate_content,
                        model=current_model,
                        contents=contents,
                        config=config_obj
                    ),
                    timeout=config.REQUEST_TIMEOUT_SECONDS
                )

                # Check if model invoked any function calls
                if response.function_calls:
                    logger.info(f"Gemini invoked {len(response.function_calls)} function call(s)")
                    # Append model's tool calls to contents
                    contents.append(response.candidates[0].content)

                    # Execute each tool call and collect results
                    tool_response_parts: List[types.Part] = []
                    for fn_call in response.function_calls:
                        tool_result = await execute_tool_call(
                            name=fn_call.name,
                            args=fn_call.args if hasattr(fn_call, "args") else {},
                            user_id=user_id,
                            scheduler_callback=scheduler_callback
                        )
                        tool_response_parts.append(
                            types.Part.from_function_response(
                                name=fn_call.name,
                                response={"result": tool_result}
                            )
                        )

                    contents.append(types.Content(role="user", parts=tool_response_parts))

                    # Make continuation call to let Biznes Sherik format final response
                    followup_response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.models.generate_content,
                            model=current_model,
                            contents=contents,
                            config=config_obj
                        ),
                        timeout=config.REQUEST_TIMEOUT_SECONDS
                    )
                    return followup_response.text or "✅ Tapsırma orınlandı."

                return response.text or ""

            except asyncio.TimeoutError:
                logger.error(f"Gemini API request timed out after {config.REQUEST_TIMEOUT_SECONDS}s")
                raise TimeoutError("Gemini API call timed out")

            except Exception as e:
                err_str = str(e)
                logger.warning(f"Gemini API attempt {attempt}/{max_retries} failed on model {current_model}: {err_str}")

                # If model is not found / deprecated for new users, fallback to gemini-3-flash-preview
                if "404" in err_str and ("no longer available" in err_str or "NOT_FOUND" in err_str) and current_model != "gemini-3-flash-preview":
                    logger.info(f"Model {current_model} unavailable, falling back to gemini-3-flash-preview...")
                    current_model = "gemini-3-flash-preview"
                    continue

                # Check if 429 (rate limit) or 503 (service unavailable)
                is_rate_limit_or_unavailable = "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str

                if attempt < max_retries and is_rate_limit_or_unavailable:
                    backoff_delay = 2 ** attempt  # 2s, 4s, 8s
                    logger.info(f"Backing off for {backoff_delay} seconds...")
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(f"Gemini API call failed permanently: {e}", exc_info=True)
                    raise e


gemini_service = GeminiService()

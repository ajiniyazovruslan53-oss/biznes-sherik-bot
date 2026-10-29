"""
Gemini function calling tools declarations and execution logic.
Supported tools:
- add_task(title, due_datetime)
- list_tasks(status)
- complete_task(task_id)
- calc_margin(cost, price, quantity, fixed_costs)
"""

from typing import Dict, Any, Optional, List
from google.genai import types
from src.db.tasks import create_task, get_tasks, complete_task as db_complete_task
from src.utils.calc import calculate_business_metrics, format_calc_summary
from src.utils.logger import logger


# Tool declarations for Gemini
GEMINI_FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="add_task",
        description="Add a new business task or action item for the user. Use this whenever the user asks to add a task, plan something to do, or dictates tasks via voice or text.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "title": types.Schema(
                    type=types.Type.STRING,
                    description="Title or concise description of the task."
                ),
                "due_datetime": types.Schema(
                    type=types.Type.STRING,
                    description="Optional ISO 8601 datetime (YYYY-MM-DD HH:MM:SS) or date (YYYY-MM-DD) when the task is due / reminder should fire. If none mentioned, pass null.",
                    nullable=True
                )
            },
            required=["title"]
        )
    ),
    types.FunctionDeclaration(
        name="list_tasks",
        description="Retrieve the current list of tasks for the user.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "status": types.Schema(
                    type=types.Type.STRING,
                    description="Task status filter: 'pending' (default), 'completed', or 'all'.",
                    enum=["pending", "completed", "all"],
                    default="pending"
                )
            }
        )
    ),
    types.FunctionDeclaration(
        name="complete_task",
        description="Mark a specific task as done/completed by its ID.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "task_id": types.Schema(
                    type=types.Type.INTEGER,
                    description="The numeric ID of the task to mark as completed."
                )
            },
            required=["task_id"]
        )
    ),
    types.FunctionDeclaration(
        name="calc_margin",
        description="Calculate unit profit, gross profit, margin %, markup %, and break-even units. Never guess numbers — use numbers provided by the user.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "cost": types.Schema(
                    type=types.Type.NUMBER,
                    description="Unit cost / self-cost (tannarx) in so'm."
                ),
                "price": types.Schema(
                    type=types.Type.NUMBER,
                    description="Unit selling price (satıw bahası) in so'm."
                ),
                "quantity": types.Schema(
                    type=types.Type.INTEGER,
                    description="Quantity of units (default 1).",
                    default=1
                ),
                "fixed_costs": types.Schema(
                    type=types.Type.NUMBER,
                    description="Total fixed overhead expenses in so'm (e.g. rent, salaries) to calculate break-even units.",
                    default=0.0
                )
            },
            required=["cost", "price"]
        )
    )
]

GEMINI_TOOLS = [types.Tool(function_declarations=GEMINI_FUNCTION_DECLARATIONS)]


async def execute_tool_call(
    name: str,
    args: Dict[str, Any],
    user_id: int,
    scheduler_callback=None
) -> Dict[str, Any]:
    """
    Executes a Gemini tool call and returns the result dictionary.
    """
    logger.info(f"Executing tool call: {name} for user_id={user_id} with args={args}")
    try:
        if name == "add_task":
            title = args.get("title", "").strip()
            due_datetime = args.get("due_datetime")
            if not title:
                return {"status": "error", "error": "Task title cannot be empty."}

            task_id = await create_task(user_id=user_id, title=title, due_datetime=due_datetime)

            # If reminder schedule callback is provided and due_datetime is given
            if scheduler_callback and due_datetime:
                try:
                    await scheduler_callback(task_id, user_id, title, due_datetime)
                except Exception as ex:
                    logger.warning(f"Could not schedule reminder for task {task_id}: {ex}")

            return {
                "status": "success",
                "task_id": task_id,
                "title": title,
                "due_datetime": due_datetime,
                "message": f"Task #{task_id} '{title}' created successfully."
            }

        elif name == "list_tasks":
            status = args.get("status", "pending")
            tasks = await get_tasks(user_id=user_id, status=status)
            return {
                "status": "success",
                "tasks_count": len(tasks),
                "tasks": [
                    {
                        "id": t["id"],
                        "title": t["title"],
                        "due_datetime": t["due_datetime"],
                        "status": t["status"]
                    }
                    for t in tasks
                ]
            }

        elif name == "complete_task":
            task_id = int(args.get("task_id", 0))
            success = await db_complete_task(task_id=task_id, user_id=user_id)
            if success:
                return {"status": "success", "task_id": task_id, "message": f"Task #{task_id} marked as completed."}
            else:
                return {"status": "error", "task_id": task_id, "error": f"Task #{task_id} not found or not owned by user."}

        elif name == "calc_margin":
            cost = float(args.get("cost", 0.0))
            price = float(args.get("price", 0.0))
            quantity = int(args.get("quantity", 1))
            fixed_costs = float(args.get("fixed_costs", 0.0))

            metrics = calculate_business_metrics(cost=cost, price=price, quantity=quantity, fixed_costs=fixed_costs)
            return {
                "status": "success",
                "metrics": metrics
            }

        else:
            return {"status": "error", "error": f"Unknown tool: {name}"}

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

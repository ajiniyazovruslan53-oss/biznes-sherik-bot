"""
Business calculation utilities:
- Margin %
- Markup %
- Profit
- Break-even units
"""

import math
from typing import Dict, Any


def calculate_business_metrics(
    cost: float,
    price: float,
    quantity: int = 1,
    fixed_costs: float = 0.0
) -> Dict[str, Any]:
    """
    Calculates key financial metrics:
    - revenue = price * quantity
    - total_cogs = cost * quantity (cost of goods sold)
    - gross_profit = revenue - total_cogs
    - margin_percentage = (gross_profit / revenue) * 100
    - markup_percentage = (gross_profit / total_cogs) * 100
    - break_even_units = ceil(fixed_costs / unit_profit) if unit_profit > 0 and fixed_costs > 0
    """
    if cost < 0 or price < 0 or quantity <= 0:
        raise ValueError("Cost and price must be non-negative, and quantity must be positive.")

    unit_profit = price - cost
    revenue = price * quantity
    total_cost = cost * quantity
    gross_profit = revenue - total_cost

    margin_pct = (unit_profit / price * 100) if price > 0 else 0.0
    markup_pct = (unit_profit / cost * 100) if cost > 0 else 0.0

    break_even_units = 0
    if fixed_costs > 0 and unit_profit > 0:
        break_even_units = math.ceil(fixed_costs / unit_profit)

    return {
        "unit_cost": cost,
        "unit_price": price,
        "unit_profit": unit_profit,
        "quantity": quantity,
        "revenue": revenue,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "margin_percentage": round(margin_pct, 2),
        "markup_percentage": round(markup_pct, 2),
        "fixed_costs": fixed_costs,
        "break_even_units": break_even_units,
    }


def format_calc_summary(metrics: Dict[str, Any], lang: str = "kaa") -> str:
    """Formats business metrics into a clear, beautiful summary table in the requested language."""
    rev = f"{metrics['revenue']:,.0f}".replace(",", " ")
    cost = f"{metrics['total_cost']:,.0f}".replace(",", " ")
    profit = f"{metrics['gross_profit']:,.0f}".replace(",", " ")
    u_cost = f"{metrics['unit_cost']:,.0f}".replace(",", " ")
    u_price = f"{metrics['unit_price']:,.0f}".replace(",", " ")
    u_profit = f"{metrics['unit_profit']:,.0f}".replace(",", " ")

    if lang == "ru":
        lines = [
            "📊 <b>Финансовый расчёт</b>:",
            f"• Цена за ед.: <code>{u_price} so'm</code>",
            f"• Себестоимость за ед.: <code>{u_cost} so'm</code>",
            f"• Прибыль с 1 шт.: <code>{u_profit} so'm</code>",
            f"• Маржинальность: <b>{metrics['margin_percentage']}%</b>",
            f"• Наценка (markup): <b>{metrics['markup_percentage']}%</b>",
        ]
        if metrics["quantity"] > 1:
            lines.extend([
                f"• Количество: {metrics['quantity']} шт.",
                f"• Выручка: <code>{rev} so'm</code>",
                f"• Общая прибыль: <code>{profit} so'm</code>",
            ])
        if metrics["break_even_units"] > 0:
            fc = f"{metrics['fixed_costs']:,.0f}".replace(",", " ")
            lines.append(f"• Точка безубыточности (при расходах {fc} so'm): <b>{metrics['break_even_units']} шт.</b>")
    elif lang == "uz":
        lines = [
            "📊 <b>Moliyaviy hisob-kitob</b>:",
            f"• Birlik narxi: <code>{u_price} so'm</code>",
            f"• Birlik tannarxi: <code>{u_cost} so'm</code>",
            f"• 1 donadan foyda: <code>{u_profit} so'm</code>",
            f"• Marja: <b>{metrics['margin_percentage']}%</b>",
            f"• Ustama (markup): <b>{metrics['markup_percentage']}%</b>",
        ]
        if metrics["quantity"] > 1:
            lines.extend([
                f"• Soni: {metrics['quantity']} dona",
                f"• Tushum: <code>{rev} so'm</code>",
                f"• Jami sof foyda: <code>{profit} so'm</code>",
            ])
        if metrics["break_even_units"] > 0:
            fc = f"{metrics['fixed_costs']:,.0f}".replace(",", " ")
            lines.append(f"• Zararsizlik nuqtasi (xarajatlar {fc} so'm): <b>{metrics['break_even_units']} dona</b>")
    else:  # Karakalpak default
        lines = [
            "📊 <b>Qarjı esap-kitabı</b>:",
            f"• Bir dana bahası: <code>{u_price} so'm</code>",
            f"• Bir dana óz bahası (tannarx): <code>{u_cost} so'm</code>",
            f"• 1 danadan payda: <code>{u_profit} so'm</code>",
            f"• Marja: <b>{metrics['margin_percentage']}%</b>",
            f"• Ustama (markup): <b>{metrics['markup_percentage']}%</b>",
        ]
        if metrics["quantity"] > 1:
            lines.extend([
                f"• Sanı: {metrics['quantity']} dana",
                f"• Túsim (túsim): <code>{rev} so'm</code>",
                f"• Jámi payda: <code>{profit} so'm</code>",
            ])
        if metrics["break_even_units"] > 0:
            fc = f"{metrics['fixed_costs']:,.0f}".replace(",", " ")
            lines.append(f"• Zıyansızlıq noqatı (qárejet {fc} so'm): <b>{metrics['break_even_units']} dana</b>")

    return "\n".join(lines)

"""
Unit tests for business calculations (calc_margin, profit, markup, break-even).
"""

import pytest
from src.utils.calc import calculate_business_metrics, format_calc_summary
from src.gemini.tools import execute_tool_call


def test_calculate_business_metrics_standard():
    # Cost = 100 000, Price = 150 000, Quantity = 10
    metrics = calculate_business_metrics(cost=100000, price=150000, quantity=10, fixed_costs=500000)

    assert metrics["unit_cost"] == 100000
    assert metrics["unit_price"] == 150000
    assert metrics["unit_profit"] == 50000
    assert metrics["revenue"] == 1500000
    assert metrics["total_cost"] == 1000000
    assert metrics["gross_profit"] == 500000
    # Margin = 50 000 / 150 000 = 33.33%
    assert metrics["margin_percentage"] == 33.33
    # Markup = 50 000 / 100 000 = 50.0%
    assert metrics["markup_percentage"] == 50.0
    # Break even = 500 000 / 50 000 = 10 units
    assert metrics["break_even_units"] == 10


def test_calculate_business_metrics_zero_cost():
    metrics = calculate_business_metrics(cost=0, price=50000, quantity=1)
    assert metrics["margin_percentage"] == 100.0
    assert metrics["markup_percentage"] == 0.0
    assert metrics["unit_profit"] == 50000


def test_calculate_business_metrics_negative_input():
    with pytest.raises(ValueError):
        calculate_business_metrics(cost=-10, price=100)


def test_format_calc_summary_all_languages():
    metrics = calculate_business_metrics(cost=80000, price=120000, quantity=5, fixed_costs=200000)

    kaa_text = format_calc_summary(metrics, lang="kaa")
    assert "Qarjı esap-kitabı" in kaa_text
    assert "Marja:" in kaa_text
    assert "33.33%" in kaa_text

    uz_text = format_calc_summary(metrics, lang="uz")
    assert "Moliyaviy hisob-kitob" in uz_text
    assert "Birlik narxi:" in uz_text

    ru_text = format_calc_summary(metrics, lang="ru")
    assert "Финансовый расчёт" in ru_text
    assert "Маржинальность:" in ru_text


@pytest.mark.asyncio
async def test_execute_tool_call_calc_margin():
    res = await execute_tool_call(
        name="calc_margin",
        args={"cost": 40000, "price": 60000, "quantity": 3, "fixed_costs": 100000},
        user_id=12345
    )
    assert res["status"] == "success"
    metrics = res["metrics"]
    assert metrics["unit_profit"] == 20000
    assert metrics["revenue"] == 180000
    assert metrics["break_even_units"] == 5

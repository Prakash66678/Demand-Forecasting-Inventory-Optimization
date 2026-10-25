
import pytest
from src.inventory_optimization import calculate_inventory_metrics


def test_inventory_metrics_returns_expected_values():
    result = calculate_inventory_metrics(
        daily_demand=[10, 12, 8, 10, 14, 10, 12],
        current_stock=100,
        lead_time_days=5,
    )
    assert result["average_daily_demand"] == 10.86
    assert result["safety_stock"] > 0
    assert result["reorder_point"] > result["lead_time_demand"]
    assert result["suggested_order_quantity"] >= 0


def test_reorder_required_when_inventory_is_low():
    result = calculate_inventory_metrics(
        daily_demand=[10, 12, 8, 10, 14, 10, 12],
        current_stock=5,
        lead_time_days=5,
    )
    assert result["reorder_required"] is True


def test_no_order_when_inventory_position_exceeds_target():
    result = calculate_inventory_metrics(
        daily_demand=[10, 12, 8, 10, 14, 10, 12],
        current_stock=1000,
        lead_time_days=5,
    )
    assert result["suggested_order_quantity"] == 0
    assert result["reorder_required"] is False


def test_negative_demand_is_rejected():
    with pytest.raises(ValueError, match="Demand"):
        calculate_inventory_metrics(
            daily_demand=[10, -2, 8],
            current_stock=100,
            lead_time_days=5,
        )


def test_invalid_service_level_is_rejected():
    with pytest.raises(ValueError, match="Service level"):
        calculate_inventory_metrics(
            daily_demand=[10, 12, 8],
            current_stock=100,
            lead_time_days=5,
            service_level=0.80,
        )

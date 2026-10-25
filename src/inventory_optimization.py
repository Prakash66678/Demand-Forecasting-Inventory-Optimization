
import numpy as np

SERVICE_LEVEL_Z = {
    0.90: 1.282,
    0.95: 1.645,
    0.99: 2.326,
}


def calculate_inventory_metrics(
    daily_demand,
    current_stock,
    lead_time_days,
    service_level=0.95,
    on_order=0,
    backorders=0,
    review_period_days=7,
):
    """Calculate safety stock, reorder point and suggested order quantity."""

    demand = np.asarray(daily_demand, dtype=float)

    if demand.ndim != 1 or len(demand) < 2:
        raise ValueError("Provide at least two daily demand values.")

    if not np.isfinite(demand).all() or (demand < 0).any():
        raise ValueError("Demand must contain finite, non-negative values.")

    if current_stock < 0 or on_order < 0 or backorders < 0:
        raise ValueError("Inventory quantities cannot be negative.")

    if lead_time_days < 1 or review_period_days < 1:
        raise ValueError("Lead time and review period must be at least 1 day.")

    if service_level not in SERVICE_LEVEL_Z:
        raise ValueError("Service level must be 0.90, 0.95, or 0.99.")

    average_daily_demand = float(np.mean(demand))
    daily_demand_std = float(np.std(demand, ddof=1))
    z_score = SERVICE_LEVEL_Z[service_level]

    # Calculate safety stock and reorder point.
    safety_stock = z_score * daily_demand_std * np.sqrt(lead_time_days)
    lead_time_demand = average_daily_demand * lead_time_days
    reorder_point = lead_time_demand + safety_stock

    # Include outstanding orders and backorders.
    inventory_position = current_stock + on_order - backorders

    # Calculate the target stock level.
    target_stock = (
        average_daily_demand * (lead_time_days + review_period_days)
        + safety_stock
    )

    suggested_order_quantity = max(
        0,
        int(np.ceil(target_stock - inventory_position)),
    )

    return {
        "average_daily_demand": round(average_daily_demand, 2),
        "daily_demand_std": round(daily_demand_std, 2),
        "lead_time_demand": round(lead_time_demand, 2),
        "safety_stock": int(np.ceil(safety_stock)),
        "reorder_point": int(np.ceil(reorder_point)),
        "inventory_position": inventory_position,
        "reorder_required": bool(inventory_position <= reorder_point),
        "suggested_order_quantity": suggested_order_quantity,
        "service_level": service_level,
    }

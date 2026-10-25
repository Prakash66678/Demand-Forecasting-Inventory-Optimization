
from pathlib import Path

import pandas as pd

from src.inventory_optimization import calculate_inventory_metrics


FORECAST_PATH = Path("reports/future_demand_forecast.csv")
SALES_PATH = Path("data/processed/forecasting_data.csv")
INVENTORY_PATH = Path("data/processed/sample_inventory_inputs.csv")
OUTPUT_PATH = Path("reports/inventory_recommendations.csv")


def generate_inventory_report():
    """Create inventory recommendations using historical demand and sample stock."""

    for path in [FORECAST_PATH, SALES_PATH, INVENTORY_PATH]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    forecasts = pd.read_csv(FORECAST_PATH, parse_dates=["date"])
    sales = pd.read_csv(SALES_PATH, parse_dates=["date"])
    inventory = pd.read_csv(INVENTORY_PATH)

    required_sales = {"date", "product_id", "units_sold"}
    required_forecasts = {"date", "product_id", "predicted_demand"}
    required_inventory = {
        "product_id",
        "current_stock",
        "lead_time_days",
        "on_order",
        "backorders",
    }

    if not required_sales.issubset(sales.columns):
        raise ValueError("Historical sales file is missing required columns.")

    if not required_forecasts.issubset(forecasts.columns):
        raise ValueError("Forecast file is missing required columns.")

    if not required_inventory.issubset(inventory.columns):
        raise ValueError("Inventory input file is missing required columns.")

    if inventory["product_id"].duplicated().any():
        raise ValueError("Inventory inputs must have one row per product.")

    results = []

    for _, stock in inventory.iterrows():
        product_id = stock["product_id"]

        historical = sales.loc[
            sales["product_id"] == product_id
        ].sort_values("date")

        future = forecasts.loc[
            forecasts["product_id"] == product_id
        ].sort_values("date")

        if len(historical) < 2:
            raise ValueError(
                f"Not enough historical demand for {product_id}."
            )

        if future.empty:
            raise ValueError(
                f"No future forecasts found for {product_id}."
            )

        lead_time = int(stock["lead_time_days"])
        current_stock = int(stock["current_stock"])
        on_order = int(stock["on_order"])
        backorders = int(stock["backorders"])

        if lead_time < 1:
            raise ValueError("Lead time must be at least one day.")

        # Use historical demand to estimate demand variability.
        metrics = calculate_inventory_metrics(
            daily_demand=historical["units_sold"].tolist(),
            current_stock=current_stock,
            lead_time_days=lead_time,
            service_level=0.95,
            on_order=on_order,
            backorders=backorders,
        )

        # Sum forecast demand over the supplier lead time.
        lead_time_forecast = future.head(lead_time)
        if len(lead_time_forecast) < lead_time:
            raise ValueError(
                f"Not enough forecast days for {product_id}."
            )

        forecast_lead_time_demand = float(
            lead_time_forecast["predicted_demand"].sum()
        )

        # Calculate a forecast-based reorder point and target stock.
        safety_stock = metrics["safety_stock"]
        reorder_point = int(
            __import__("math").ceil(
                forecast_lead_time_demand + safety_stock
            )
        )

        review_days = 7
        target_period = future.head(lead_time + review_days)

        if len(target_period) < lead_time + review_days:
            raise ValueError(
                f"Not enough forecast days for target stock of {product_id}."
            )

        target_stock = int(
            __import__("math").ceil(
                target_period["predicted_demand"].sum() + safety_stock
            )
        )

        inventory_position = current_stock + on_order - backorders

        suggested_order = max(
            0, target_stock - inventory_position
        )

        results.append(
            {
                "product_id": product_id,
                "current_stock": current_stock,
                "on_order": on_order,
                "backorders": backorders,
                "inventory_position": inventory_position,
                "lead_time_days": lead_time,
                "forecast_lead_time_demand": round(
                    forecast_lead_time_demand, 2
                ),
                "safety_stock": safety_stock,
                "reorder_point": reorder_point,
                "reorder_required": bool(
                    inventory_position <= reorder_point
                ),
                "target_stock": target_stock,
                "suggested_order_quantity": suggested_order,
                "selected_model": (
                    future["selected_model"].iloc[0]
                    if "selected_model" in future.columns
                    else "Unknown"
                ),
                "inventory_data_type": "Sample inputs - replace with real data",
            }
        )

    report = pd.DataFrame(results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT_PATH, index=False)

    print("\nInventory recommendations:")
    print(report.to_string(index=False))
    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_inventory_report()

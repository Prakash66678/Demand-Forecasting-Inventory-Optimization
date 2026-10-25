
from pathlib import Path

import numpy as np
import pandas as pd

from src.forecasting import (
    moving_average_forecast,
    seasonal_naive_forecast,
)

DATA_PATH = Path("data/processed/forecasting_data.csv")
RESULTS_PATH = Path("reports/forecast_model_comparison.csv")
OUTPUT_PATH = Path("reports/future_demand_forecast.csv")

FORECAST_DAYS = 30


def forecast_with_model(train, model_name, horizon):
    """Generate future predictions using the selected model."""

    train = np.asarray(train, dtype=float)

    if model_name == "Naive":
        predictions = np.repeat(train[-1], horizon)

    elif model_name == "Moving Average (7-day)":
        predictions = moving_average_forecast(
            train, horizon, window=7
        )

    elif model_name == "Seasonal Naive (7-day)":
        predictions = seasonal_naive_forecast(
            train, horizon, season_length=7
        )

    elif model_name == "Holt-Winters":
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        )
        fitted_model = model.fit()
        predictions = fitted_model.forecast(horizon)

    else:
        raise ValueError(f"Unknown forecasting model: {model_name}")

    # Demand cannot be negative.
    return np.maximum(np.asarray(predictions, dtype=float), 0)


def generate_future_forecasts():
    """Select each product's best model and forecast 30 days."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Model comparison not found: {RESULTS_PATH}"
        )

    data = pd.read_csv(DATA_PATH, parse_dates=["date"])
    results = pd.read_csv(RESULTS_PATH)

    forecasts = []

    for product_id, product_data in data.groupby("product_id"):
        product_data = product_data.sort_values("date")
        values = product_data["units_sold"].to_numpy(dtype=float)

        if len(values) == 0:
            continue

        product_results = results[
            results["product_id"] == product_id
        ].dropna(subset=["MAE"])

        if product_results.empty:
            print(f"Skipping {product_id}: no valid model results.")
            continue

        # The model with the lowest test MAE is selected.
        ranked_models = product_results.sort_values("MAE")

        predictions = None
        selected_model = None

        # If the top model fails to fit, try the next ranked model.
        for _, row in ranked_models.iterrows():
            model_name = row["model"]

            try:
                predictions = forecast_with_model(
                    values, model_name, FORECAST_DAYS
                )
                selected_model = model_name
                break
            except Exception as error:
                print(
                    f"{model_name} failed for {product_id}: {error}"
                )

        if predictions is None:
            print(f"Skipping {product_id}: all models failed.")
            continue

        last_date = product_data["date"].max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=FORECAST_DAYS,
            freq="D",
        )

        for date, prediction in zip(future_dates, predictions):
            forecasts.append({
                "date": date,
                "product_id": product_id,
                "predicted_demand": round(float(prediction), 2),
                "selected_model": selected_model,
            })

    if not forecasts:
        raise ValueError("No forecasts were generated.")

    forecast_df = pd.DataFrame(forecasts)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(OUTPUT_PATH, index=False)

    return forecast_df


if __name__ == "__main__":
    forecast_df = generate_future_forecasts()

    print("\nFuture demand forecast generated successfully!")
    print(f"Forecast rows: {len(forecast_df)}")
    print("\nSelected models:")
    print(
        forecast_df[["product_id", "selected_model"]]
        .drop_duplicates()
        .to_string(index=False)
    )
    print("\nFirst forecast rows:")
    print(forecast_df.head(10).to_string(index=False))
    print(f"\nSaved to: {OUTPUT_PATH}")


from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

DATA_PATH = Path("data/processed/forecasting_data.csv")
RESULT_PATH = Path("reports/forecast_model_comparison.csv")

TEST_FRACTION = 0.20
SEASON_LENGTH = 7


def moving_average_forecast(train, horizon, window=7):
    """Forecast future values using the latest rolling average."""
    history = list(train)
    predictions = []

    for _ in range(horizon):
        prediction = float(np.mean(history[-window:]))
        predictions.append(prediction)
        history.append(prediction)

    return np.array(predictions)


def seasonal_naive_forecast(train, horizon, season_length=7):
    """Repeat the latest observed weekly pattern."""
    train = np.asarray(train, dtype=float)

    if len(train) < season_length:
        raise ValueError("Not enough training data for seasonal naive.")

    return np.resize(train[-season_length:], horizon)


def evaluate_forecast(actual, predicted):
    """Calculate standard forecasting error metrics."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    # MAPE is undefined when actual demand is zero.
    nonzero = actual != 0
    if nonzero.any():
        mape = np.mean(
            np.abs(
                (actual[nonzero] - predicted[nonzero])
                / actual[nonzero]
            )
        ) * 100
    else:
        mape = np.nan

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE_percent": mape,
    }


def compare_models(data):
    """Compare forecasting models using a chronological test split."""
    results = []

    for product_id, product_data in data.groupby("product_id"):
        product_data = product_data.sort_values("date")
        values = product_data["units_sold"].to_numpy(dtype=float)

        split_index = int(len(values) * (1 - TEST_FRACTION))
        train = values[:split_index]
        test = values[split_index:]

        if len(train) < 2 or len(test) == 0:
            print(f"Skipping {product_id}: not enough data.")
            continue

        predictions = {
            "Naive": np.repeat(train[-1], len(test)),
            "Moving Average (7-day)": moving_average_forecast(
                train, len(test)
            ),
            "Seasonal Naive (7-day)": seasonal_naive_forecast(
                train, len(test)
            ),
        }

        # Optional statistical model. Other models still work if
        # Holt-Winters cannot fit the data.
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing

            model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=SEASON_LENGTH,
                initialization_method="estimated",
            )
            fitted_model = model.fit()
            predictions["Holt-Winters"] = fitted_model.forecast(
                len(test)
            )
        except Exception as error:
            print(
                f"Holt-Winters skipped for {product_id}: {error}"
            )

        for model_name, predicted in predictions.items():
            metrics = evaluate_forecast(test, predicted)

            results.append({
                "product_id": product_id,
                "model": model_name,
                "train_rows": len(train),
                "test_rows": len(test),
                **metrics,
            })

    return pd.DataFrame(results)


if __name__ == "__main__":
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}. "
            "Run python -m src.prepare_forecasting_data first."
        )

    df = pd.read_csv(DATA_PATH, parse_dates=["date"])

    required = {"date", "product_id", "units_sold"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"Dataset must contain these columns: {sorted(required)}"
        )

    results = compare_models(df)

    if results.empty:
        raise ValueError("No forecasting results were produced.")

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULT_PATH, index=False)

    print("\nForecasting model comparison:")
    print(
        results.sort_values(["product_id", "MAE"]).to_string(
            index=False
        )
    )
    print(f"\nResults saved to: {RESULT_PATH}")

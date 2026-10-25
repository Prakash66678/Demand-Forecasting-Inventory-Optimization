
import numpy as np
import pandas as pd

from src.forecasting import (
    moving_average_forecast,
    seasonal_naive_forecast,
    evaluate_forecast,
    compare_models,
)


def test_moving_average_forecast():
    train = [10, 20, 30, 40, 50, 60, 70]

    predictions = moving_average_forecast(train, horizon=2)

    assert len(predictions) == 2
    assert predictions[0] == 40.0


def test_seasonal_naive_forecast():
    train = [10, 20, 30, 40, 50, 60, 70]

    predictions = seasonal_naive_forecast(train, horizon=10)

    assert len(predictions) == 10
    assert predictions.tolist() == [
        10, 20, 30, 40, 50, 60, 70, 10, 20, 30
    ]


def test_evaluate_forecast():
    actual = [10, 20, 30]
    predicted = [12, 18, 33]

    metrics = evaluate_forecast(actual, predicted)

    assert np.isclose(metrics["MAE"], 7 / 3)
    assert metrics["RMSE"] > 0
    assert np.isfinite(metrics["MAPE_percent"])


def test_compare_models_uses_chronological_split():
    dates = pd.date_range("2025-01-01", periods=60, freq="D")

    data = pd.DataFrame({
        "date": dates,
        "product_id": ["P001"] * 60,
        "units_sold": [
            50 + (i % 7) * 2 + i * 0.1
            for i in range(60)
        ],
    })

    results = compare_models(data)

    assert not results.empty
    assert set(results["product_id"]) == {"P001"}
    assert set(results["train_rows"]) == {48}
    assert set(results["test_rows"]) == {12}
    assert "Naive" in results["model"].values
    assert (results["MAE"] >= 0).all()

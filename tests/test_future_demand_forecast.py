
import numpy as np
import pytest

from src.predict_future_demand import forecast_with_model


def test_naive_forecast_returns_requested_days():
    predictions = forecast_with_model(
        [10, 20, 30], "Naive", horizon=5
    )

    assert len(predictions) == 5
    assert np.all(predictions == 30)


def test_moving_average_forecast_returns_requested_days():
    predictions = forecast_with_model(
        [10, 20, 30, 40, 50, 60, 70],
        "Moving Average (7-day)",
        horizon=10,
    )

    assert len(predictions) == 10
    assert np.all(predictions >= 0)


def test_seasonal_naive_forecast_returns_requested_days():
    predictions = forecast_with_model(
        [10, 20, 30, 40, 50, 60, 70],
        "Seasonal Naive (7-day)",
        horizon=14,
    )

    assert len(predictions) == 14
    assert predictions.tolist() == [
        10, 20, 30, 40, 50, 60, 70,
        10, 20, 30, 40, 50, 60, 70,
    ]


def test_unknown_model_raises_error():
    with pytest.raises(ValueError, match="Unknown forecasting model"):
        forecast_with_model([10, 20, 30], "Unknown Model", 5)


import pandas as pd
import pytest

from src.data_cleaning import clean_sales_data


def test_clean_sales_data_removes_invalid_rows():
    df = pd.DataFrame({
        "date": ["2025-01-01", "invalid", "2025-01-03"],
        "product_id": ["P001", "P001", "P002"],
        "units_sold": [10, 20, -5],
    })

    result = clean_sales_data(df)

    assert len(result) == 1
    assert result.iloc[0]["units_sold"] == 10


def test_duplicate_daily_sales_are_summed():
    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01"],
        "product_id": ["P001", "P001"],
        "units_sold": [10, 5],
    })

    result = clean_sales_data(df)

    assert len(result) == 1
    assert result.iloc[0]["units_sold"] == 15


def test_missing_required_column_raises_error():
    df = pd.DataFrame({
        "date": ["2025-01-01"],
        "product_id": ["P001"],
    })

    with pytest.raises(ValueError):
        clean_sales_data(df)

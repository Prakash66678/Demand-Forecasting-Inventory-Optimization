
from pathlib import Path

import pandas as pd

from src.data_cleaning import clean_sales_data


RAW_DATA_PATH = Path("data/raw/retail_demand.csv")
CLEAN_DATA_PATH = Path("data/interim/retail_demand_clean.csv")
OUTPUT_PATH = Path("data/processed/forecasting_data.csv")


def prepare_forecasting_data() -> pd.DataFrame:
    """Prepare cleaned daily demand data for time-series forecasting."""

    # Reuse the data-cleaning function from Week 1.
    if CLEAN_DATA_PATH.exists():
        df = pd.read_csv(CLEAN_DATA_PATH)
    elif RAW_DATA_PATH.exists():
        df = pd.read_csv(RAW_DATA_PATH)
    else:
        raise FileNotFoundError(
            "No dataset found in data/raw or data/interim."
        )

    # Validate and clean the data using the Week 1 function.
    df = clean_sales_data(df)

    # Ensure each product's records are in date order.
    df = df.sort_values(
        ["product_id", "date"]
    ).reset_index(drop=True)

    # Create the output folder if it does not exist.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save a separate file for forecasting.
    df.to_csv(OUTPUT_PATH, index=False)

    return df


if __name__ == "__main__":
    forecasting_df = prepare_forecasting_data()

    print("Forecasting data prepared successfully!")
    print(f"Rows: {len(forecasting_df)}")
    print(f"Products: {forecasting_df['product_id'].nunique()}")
    print(f"Saved to: {OUTPUT_PATH}")
    print(forecasting_df.head())

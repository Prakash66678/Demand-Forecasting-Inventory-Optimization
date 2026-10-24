
import pandas as pd


REQUIRED_COLUMNS = ["date", "product_id", "units_sold"]


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean daily product-sales records."""

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    cleaned = df[REQUIRED_COLUMNS].copy()

    cleaned["date"] = pd.to_datetime(
        cleaned["date"], errors="coerce"
    )
    cleaned["product_id"] = (
        cleaned["product_id"].astype("string").str.strip()
    )
    cleaned["units_sold"] = pd.to_numeric(
        cleaned["units_sold"], errors="coerce"
    )

    cleaned = cleaned.dropna(
        subset=["date", "product_id", "units_sold"]
    )
    cleaned = cleaned[cleaned["product_id"] != ""]
    cleaned = cleaned[cleaned["units_sold"] >= 0]

    # A daily product series should have at most one record
    # per product and date. Resolve duplicates by summing sales.
    cleaned = (
        cleaned.groupby(
            ["date", "product_id"], as_index=False
        )["units_sold"].sum()
    )

    return cleaned.sort_values(
        ["product_id", "date"]
    ).reset_index(drop=True)

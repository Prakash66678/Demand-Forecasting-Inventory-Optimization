
from pathlib import Path
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION AND THEME
# ============================================================

st.set_page_config(
    page_title="DemandPilot AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            145deg, #0b1120 0%, #101a30 55%, #111827 100%
        );
        color: #f1f5f9;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #0a1020;
        border-right: 1px solid #263449;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #17243a, #111c2f);
        border: 1px solid #2b3c55;
        padding: 18px;
        border-radius: 16px;
    }

    [data-testid="stMetricLabel"] {
        color: #a8bad1;
    }

    [data-testid="stMetricValue"] {
        color: #e2e8f0;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid #3b82f6;
        min-height: 44px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #60a5fa;
        color: #93c5fd;
        transform: translateY(-1px);
    }

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    h1, h2, h3 {
        letter-spacing: -0.5px;
    }

    hr {
        border-color: #2b3c55;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. PATHS AND COLUMN DEFINITIONS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DEMO_PATH = BASE_DIR / "data" / "raw" / "retail_demand.csv"

REQUIRED_FIELDS = ["date", "product_id", "units_sold"]

COLUMN_ALIASES = {
    "date": [
        "date", "order_date", "sales_date", "transaction_date"
    ],
    "product_id": [
        "product_id", "product", "sku", "item_id"
    ],
    "units_sold": [
        "units_sold", "demand", "quantity",
        "sales_quantity", "units", "qty"
    ],
    "store_id": [
        "store_id", "store", "location_id"
    ],
    "current_stock": [
        "current_stock", "stock", "inventory", "on_hand"
    ],
    "lead_time_days": [
        "lead_time_days", "lead_time", "leadtime"
    ],
    "on_order": [
        "on_order", "purchase_orders", "incoming_stock"
    ],
    "backorders": [
        "backorders", "backorder", "pending_orders"
    ],
    "price": [
        "price", "unit_price", "selling_price"
    ],
    "promo": [
        "promo", "promotion", "is_promo"
    ],
}


# ============================================================
# 3. DATA LOADING
# ============================================================

def read_uploaded_file(uploaded_file):
    """Read uploaded CSV or Excel files."""

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if filename.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")

    if filename.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    raise ValueError("Please upload a CSV, XLSX, or XLS file.")


def load_demo_data():
    """Load the bundled demonstration dataset."""

    if not DEMO_PATH.exists():
        raise FileNotFoundError(
            f"Demo dataset not found: {DEMO_PATH}"
        )

    return pd.read_csv(DEMO_PATH)


# ============================================================
# 4. COLUMN MAPPING
# ============================================================

def suggest_column(columns, field):
    """Suggest matching columns based on normalized names."""

    def normalize(value):
        return "".join(
            char
            for char in str(value).strip().lower()
            if char.isalnum()
        )

    lookup = {
        normalize(column): column
        for column in columns
    }

    for alias in COLUMN_ALIASES.get(field, []):
        normalized_alias = normalize(alias)

        if normalized_alias in lookup:
            return lookup[normalized_alias]

    return None


def map_columns(df, mapping):
    """Standardize selected source columns."""

    output = pd.DataFrame(index=df.index)

    for standard_name, source_name in mapping.items():
        if source_name is not None:
            output[standard_name] = df[source_name].copy()

    return output.reset_index(drop=True)


# ============================================================
# 5. DATA QUALITY VALIDATION
# ============================================================

def validate_data(df):
    """Identify common data-quality problems."""

    missing_columns = [
        column
        for column in REQUIRED_FIELDS
        if column not in df.columns
    ]

    if missing_columns:
        return pd.DataFrame([
            {
                "Check": "Required columns",
                "Count": len(missing_columns),
                "Details": ", ".join(missing_columns),
            }
        ])

    dates = pd.to_datetime(df["date"], errors="coerce")
    products = df["product_id"].astype("string").str.strip()
    demand = pd.to_numeric(df["units_sold"], errors="coerce")

    temp = pd.DataFrame({
        "_date": dates,
        "_product": products,
    })

    valid_keys = temp["_date"].notna() & temp["_product"].notna()

    duplicate_count = int(
        temp.loc[valid_keys].duplicated(
            ["_date", "_product"]
        ).sum()
    )

    checks = [
        (
            "Invalid dates",
            int(dates.isna().sum()),
            "Missing or unrecognizable date values",
        ),
        (
            "Missing product IDs",
            int(products.isna().sum()),
            "Rows without a product identifier",
        ),
        (
            "Blank product IDs",
            int((products.notna() & products.eq("")).sum()),
            "Rows with empty product identifiers",
        ),
        (
            "Invalid demand",
            int(demand.isna().sum()),
            "Missing or non-numeric demand values",
        ),
        (
            "Negative demand",
            int((demand < 0).sum()),
            "Negative demand values",
        ),
        (
            "Duplicate date-product rows",
            duplicate_count,
            "Repeated product/date combinations",
        ),
    ]

    return pd.DataFrame([
        {
            "Check": name,
            "Count": count,
            "Details": details,
        }
        for name, count, details in checks
    ])


def prepare_demand_data(df):
    """Clean demand data and aggregate duplicate product/date rows."""

    missing = [
        column
        for column in REQUIRED_FIELDS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Please map the required fields: "
            + ", ".join(missing)
        )

    data = df.copy()

    data["date"] = pd.to_datetime(
        data["date"], errors="coerce"
    )

    data["product_id"] = (
        data["product_id"].astype("string").str.strip()
    )

    data["units_sold"] = pd.to_numeric(
        data["units_sold"], errors="coerce"
    )

    data = data.dropna(subset=REQUIRED_FIELDS)

    data = data[
        (data["product_id"] != "")
        & (data["units_sold"] >= 0)
    ].copy()

    data = data.groupby(
        ["date", "product_id"],
        as_index=False,
    )["units_sold"].sum()

    return data.sort_values(
        ["date", "product_id"]
    ).reset_index(drop=True)


# ============================================================
# 6. LANDING PAGE
# ============================================================

def render_landing_page():
    st.markdown(
        """
        <div style="padding: 26px 4px 18px 4px;">
            <p style="
                color: #60A5FA;
                font-weight: 700;
                letter-spacing: 3px;
                font-size: 14px;
            ">DEMANDPILOT AI</p>

            <h1 style="
                font-size: clamp(34px, 5vw, 54px);
                line-height: 1.15;
            ">
                Predict Demand.<br>
                Optimize Inventory.<br>
                Make Smarter Decisions.
            </h1>

            <p style="
                font-size: 18px;
                color: #A8BAD1;
                max-width: 760px;
                line-height: 1.7;
            ">
                Explore demand patterns, analyze products,
                and make inventory decisions using your data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        if st.button(
            "🚀 Launch Analytics",
            type="primary",
            width="stretch",
        ):
            st.session_state["launched"] = True
            st.rerun()

    with right:
        if st.button(
            "📊 Explore Demo",
            width="stretch",
        ):
            st.session_state["launched"] = True
            st.session_state["use_demo"] = True
            st.rerun()

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 📈 Forecasting")
        st.write("Explore historical demand patterns.")

    with c2:
        st.markdown("### 📦 Inventory")
        st.write("Review product demand for inventory planning.")

    with c3:
        st.markdown("### 🔍 Data Quality")
        st.write("Inspect invalid records and data-quality issues.")

    st.info(
        "Upload your own dataset or use the bundled demo dataset. "
        "Demo data does not represent verified business inventory."
    )


# ============================================================
# 7. SESSION STATE
# ============================================================

if "launched" not in st.session_state:
    st.session_state["launched"] = False

if "use_demo" not in st.session_state:
    st.session_state["use_demo"] = True


# ============================================================
# 8. SIDEBAR AND DATA SOURCE
# ============================================================

st.title("📦 DemandPilot AI")
st.caption(
    "Intelligent Demand Forecasting & Inventory Optimization"
)

with st.sidebar:
    st.markdown("## 🧭 Dashboard Guide")
    st.caption(
        "All dashboards appear on one page. Scroll down to explore."
    )

    st.divider()
    st.markdown("### 📁 Data Source")

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=["csv", "xlsx", "xls"],
        help="Required fields: date, product ID, and units sold.",
    )

    use_demo = st.checkbox(
        "Use bundled demo dataset",
        value=st.session_state["use_demo"],
    )

    st.session_state["use_demo"] = use_demo

    st.divider()
    st.caption("Project: DemandPilot AI")


# ============================================================
# 9. LANDING PAGE DISPLAY
# ============================================================

if (
    not st.session_state["launched"]
    and uploaded_file is None
):
    render_landing_page()
    st.stop()


# ============================================================
# 10. LOAD DATA
# ============================================================

try:
    if uploaded_file is not None:
        raw_data = read_uploaded_file(uploaded_file)
        source_label = f"Uploaded file: {uploaded_file.name}"

    elif st.session_state["use_demo"]:
        raw_data = load_demo_data()
        source_label = "Bundled demonstration dataset"

    else:
        st.warning(
            "Upload a dataset or enable the bundled demo dataset."
        )
        st.stop()

except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()


if raw_data.empty:
    st.error("The selected dataset contains no rows.")
    st.stop()

st.caption(f"**Current data source:** {source_label}")


# ============================================================
# 11. AUTO MAPPING AND MANUAL MAPPING
# ============================================================

st.header("⚙️ Configure Your Data")

if uploaded_file is not None:
    upload_key = (
        str(uploaded_file.name)
        .replace(".", "_")
        .replace(" ", "_")
    )

    auto_mapping_enabled = st.toggle(
        "✨ Enable Auto Mapping",
        value=False,
        key=f"auto_mapping_{upload_key}",
    )
else:
    auto_mapping_enabled = True
    st.info("Automatic mapping is enabled for the demo dataset.")


mapping = {}

with st.expander(
    "Review and configure column mapping",
    expanded=True,
):
    for field in COLUMN_ALIASES:
        options = ["(Not mapped)"] + list(raw_data.columns)

        if auto_mapping_enabled:
            suggested = suggest_column(raw_data.columns, field)
            default_index = (
                options.index(suggested)
                if suggested in raw_data.columns
                else 0
            )
        else:
            default_index = 0

        selected = st.selectbox(
            f"{field}" + (
                " *" if field in REQUIRED_FIELDS else ""
            ),
            options,
            index=default_index,
            key=(
                f"column_{upload_key if uploaded_file else 'demo'}"
                f"_{field}_{auto_mapping_enabled}"
            ),
        )

        mapping[field] = (
            None if selected == "(Not mapped)" else selected
        )

    st.caption("* Required fields")


mapped_data = map_columns(raw_data, mapping)

missing_required = [
    field
    for field in REQUIRED_FIELDS
    if field not in mapped_data.columns
]

if missing_required:
    st.warning(
        "Map the required fields before continuing: "
        + ", ".join(missing_required)
    )
    st.stop()


# ============================================================
# 12. VALIDATE AND CLEAN DATA
# ============================================================

quality = validate_data(mapped_data)

try:
    clean_data = prepare_demand_data(mapped_data)
except Exception as exc:
    st.error(f"Could not prepare the data: {exc}")
    st.stop()

if clean_data.empty:
    st.error(
        "No valid demand rows remain after cleaning. "
        "Check the date, product ID, and demand columns."
    )
    st.stop()

st.success(
    f"Dataset ready: {len(clean_data):,} cleaned records."
)


# ============================================================
# 13. DASHBOARD 1 — DEMAND OVERVIEW
# ============================================================

st.divider()
st.header("📈 1. Demand Overview")

st.write(
    "Explore historical demand, product performance, "
    "and daily demand patterns."
)

products = sorted(
    clean_data["product_id"].astype(str).unique().tolist()
)

selected_products = st.multiselect(
    "Filter products in Demand Overview",
    products,
    default=products,
    key="overview_product_filter",
)

view = clean_data[
    clean_data["product_id"].astype(str).isin(selected_products)
].copy()

if view.empty:
    st.warning("Select at least one product.")
else:
    daily_totals = view.groupby(
        "date", as_index=False
    )["units_sold"].sum()

    total_demand = view["units_sold"].sum()
    average_daily_demand = daily_totals["units_sold"].mean()

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Demand", f"{total_demand:,.0f} units")
    m2.metric("Products", f"{view['product_id'].nunique():,}")
    m3.metric(
        "Average Daily Demand",
        f"{average_daily_demand:,.1f}",
    )
    m4.metric("Product-Date Records", f"{len(view):,}")

    left, right = st.columns(2)

    with left:
        st.subheader("Daily Demand Trend")

        st.plotly_chart(
            px.line(
                daily_totals,
                x="date",
                y="units_sold",
                markers=True,
                title="Total Daily Demand",
                labels={
                    "date": "Date",
                    "units_sold": "Units Sold",
                },
                template="plotly_dark",
            ),
            width="stretch",
        )

    with right:
        st.subheader("Demand by Product")

        product_totals = view.groupby(
            "product_id", as_index=False
        )["units_sold"].sum()

        st.plotly_chart(
            px.bar(
                product_totals,
                x="product_id",
                y="units_sold",
                title="Total Demand by Product",
                labels={
                    "product_id": "Product",
                    "units_sold": "Units Sold",
                },
                template="plotly_dark",
            ),
            width="stretch",
        )

    st.subheader("Historical Demand Data")
    st.dataframe(view, width="stretch", hide_index=True)


# ============================================================
# 14. DASHBOARD 2 — DEMAND FORECASTING
# ============================================================

st.divider()
st.header("📊 2. Demand Forecasting")

st.write(
    "Examine historical demand patterns that can be used "
    "as input for future forecasting."
)

forecast_daily = clean_data.groupby(
    "date", as_index=False
)["units_sold"].sum()

st.plotly_chart(
    px.line(
        forecast_daily,
        x="date",
        y="units_sold",
        markers=True,
        title="Historical Demand for Forecasting",
        labels={
            "date": "Date",
            "units_sold": "Units Sold",
        },
        template="plotly_dark",
    ),
    width="stretch",
)

st.subheader("Daily Historical Demand")
st.dataframe(
    forecast_daily,
    width="stretch",
    hide_index=True,
)

st.info(
    "This section currently displays historical demand. "
    "Future predictions will appear after your forecasting "
    "module is connected."
)


# ============================================================
# 15. DASHBOARD 3 — INVENTORY INTELLIGENCE
# ============================================================

st.divider()
st.header("📦 3. Inventory Intelligence")

st.write(
    "Review demand by product to support inventory planning."
)

inventory_summary = clean_data.groupby(
    "product_id", as_index=False
).agg(
    total_demand=("units_sold", "sum"),
    average_record_demand=("units_sold", "mean"),
    demand_records=("units_sold", "count"),
).sort_values("total_demand", ascending=False)

st.plotly_chart(
    px.bar(
        inventory_summary,
        x="product_id",
        y="total_demand",
        title="Product Demand for Inventory Planning",
        labels={
            "product_id": "Product",
            "total_demand": "Total Demand",
        },
        template="plotly_dark",
    ),
    width="stretch",
)

st.subheader("Inventory Planning Data")
st.dataframe(
    inventory_summary,
    width="stretch",
    hide_index=True,
)

st.info(
    "Safety stock, reorder points, and stockout risk are not "
    "calculated yet. These require inventory inputs and "
    "connected inventory calculation logic."
)


# ============================================================
# 16. DASHBOARD 4 — MODEL PERFORMANCE
# ============================================================

st.divider()
st.header("🎯 4. Model Performance")

st.write(
    "This section will report how accurately a forecasting "
    "model predicts demand."
)

st.info(
    "Connect your model evaluation module to show real metrics "
    "such as MAE and RMSE. No performance scores are invented."
)


# ============================================================
# 17. DASHBOARD 5 — DATA QUALITY AND INSIGHTS
# ============================================================

st.divider()
st.header("🔍 5. Data Quality & Insights")

c1, c2, c3 = st.columns(3)

c1.metric("Original Rows", f"{len(raw_data):,}")
c2.metric("Mapped Rows", f"{len(mapped_data):,}")
c3.metric("Cleaned Rows", f"{len(clean_data):,}")

st.subheader("Validation Results")

st.dataframe(
    quality,
    width="stretch",
    hide_index=True,
)

st.subheader("Cleaned Demand Dataset")

st.dataframe(
    clean_data,
    width="stretch",
    hide_index=True,
)


# ============================================================
# 18. DEMANDPILOT AI CHATBOT
# ============================================================

st.divider()
st.header("🤖 DemandPilot AI Assistant")

try:
    from chatbot import render_demandpilot_chatbot

    render_demandpilot_chatbot(clean_data)

except ImportError as exc:
    st.warning(
        "The chatbot could not be imported. Check that chatbot.py "
        "exists and its required packages are installed."
    )
    st.caption(str(exc))


# ============================================================
# 19. DOWNLOAD ALL DASHBOARD DATA
# ============================================================

st.divider()
st.header("📥 Download All Dashboard Data")

st.write(
    "Export your source data, cleaned data, quality report, "
    "and demand summaries into one Excel workbook."
)


def create_dashboard_excel():
    """Create an Excel workbook with all currently available data."""

    output = BytesIO()

    product_summary = clean_data.groupby(
        "product_id", as_index=False
    ).agg(
        total_demand=("units_sold", "sum"),
        average_record_demand=("units_sold", "mean"),
        demand_records=("units_sold", "count"),
    ).sort_values("total_demand", ascending=False)

    daily_summary = clean_data.groupby(
        "date", as_index=False
    )["units_sold"].sum()

    monthly_data = clean_data.copy()
    monthly_data["month"] = (
        pd.to_datetime(monthly_data["date"])
        .dt.to_period("M")
        .astype(str)
    )

    monthly_summary = monthly_data.groupby(
        "month", as_index=False
    )["units_sold"].sum()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        raw_data.to_excel(
            writer,
            sheet_name="Original Data",
            index=False,
        )

        mapped_data.to_excel(
            writer,
            sheet_name="Mapped Data",
            index=False,
        )

        clean_data.to_excel(
            writer,
            sheet_name="Cleaned Data",
            index=False,
        )

        quality.to_excel(
            writer,
            sheet_name="Data Quality",
            index=False,
        )

        product_summary.to_excel(
            writer,
            sheet_name="Product Summary",
            index=False,
        )

        daily_summary.to_excel(
            writer,
            sheet_name="Daily Demand",
            index=False,
        )

        monthly_summary.to_excel(
            writer,
            sheet_name="Monthly Demand",
            index=False,
        )

    output.seek(0)
    return output.getvalue()


try:
    excel_bytes = create_dashboard_excel()

    st.download_button(
        label="📥 Download All Dashboard Data (Excel)",
        data=excel_bytes,
        file_name="DemandPilot_All_Dashboard_Data.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
        width="stretch",
    )

    st.caption(
        "The workbook contains seven sheets: Original Data, "
        "Mapped Data, Cleaned Data, Data Quality, Product Summary, "
        "Daily Demand, and Monthly Demand."
    )

except Exception as exc:
    st.error(f"Could not prepare the Excel workbook: {exc}")

st.divider()

st.caption(
    "DemandPilot AI | Demand Forecasting & Inventory Optimization"
)

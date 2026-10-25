
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION AND CREATIVE THEME
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
    """Read CSV or Excel data without changing the uploaded file."""

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if filename.endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(uploaded_file)
        except ImportError as exc:
            raise ValueError(
                "Excel support requires an Excel reader package. "
                "For .xlsx files, run: "
                "python -m pip install openpyxl"
            ) from exc

    raise ValueError("Please upload a CSV, XLSX, or XLS file.")


def load_demo_data():
    """Load the bundled demonstration dataset."""

    if not DEMO_PATH.exists():
        raise FileNotFoundError(
            f"Demo dataset not found: {DEMO_PATH}"
        )

    return pd.read_csv(DEMO_PATH)


# ============================================================
# 4. AUTOMATIC AND MANUAL COLUMN MAPPING
# ============================================================


def suggest_column(columns, field):
    """Suggest a source column using normalized column names."""

    def normalize(value):
        return "".join(
            character
            for character in str(value).strip().lower()
            if character.isalnum()
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
    """Create a standardized dataset using selected source columns."""

    output = pd.DataFrame(index=df.index)

    for standard_name, source_name in mapping.items():
        if source_name is not None:
            output[standard_name] = df[source_name].copy()

    return output.reset_index(drop=True)


# ============================================================
# 5. DATA QUALITY VALIDATION
# ============================================================

def validate_data(df):
    """Return a transparent summary of data-quality issues."""

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

    nonblank_products = products.fillna("").ne("")

    temp = pd.DataFrame({
        "_date": dates,
        "_product": products,
    })

    valid_key_rows = temp["_date"].notna() & temp["_product"].notna()

    duplicate_count = int(
        temp.loc[valid_key_rows].duplicated(
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
            int((products.notna() & ~nonblank_products).sum()),
            "Rows with an empty product identifier",
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
    """Clean a working copy for demand analysis."""

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

    # Aggregate duplicate records to one demand value per
    # product and date, matching the existing project structure.
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
        <div style="
            padding: 26px 4px 18px 4px;
            border-radius: 20px;
        ">
            <p style="
                color: #60A5FA;
                font-weight: 700;
                letter-spacing: 3px;
                font-size: 14px;
            ">
                DEMANDPILOT AI
            </p>

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
                Explore demand patterns, compare forecasts,
                and make inventory decisions using transparent
                calculations and your own data.
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
            st.session_state["page"] = "Demand Overview"
            st.session_state["launched"] = True
            st.rerun()

    with right:
        if st.button(
            "📊 Explore Demo",
            width="stretch",
        ):
            st.session_state["use_demo"] = True
            st.session_state["page"] = "Demand Overview"
            st.session_state["launched"] = True
            st.rerun()

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 📈 Forecasting")
        st.write(
            "Explore historical demand and prepare for "
            "forecast evaluation."
        )

    with c2:
        st.markdown("### 📦 Inventory")
        st.write(
            "Review inventory inputs and transparent "
            "replenishment calculations."
        )

    with c3:
        st.markdown("### 🔍 Data Quality")
        st.write(
            "Inspect missing values, invalid records, "
            "and duplicate observations."
        )

    st.info(
        "Start with the bundled demo dataset or upload your own. "
        "Demonstration inventory values are examples, not "
        "verified business stock records."
    )


# ============================================================
# 7. SESSION STATE AND SIDEBAR
# ============================================================

PAGES = [
    "Home",
    "Demand Overview",
    "Demand Forecasting",
    "Inventory Intelligence",
    "Model Performance",
    "Data Quality & Insights",
]

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

if "launched" not in st.session_state:
    st.session_state["launched"] = False

if "use_demo" not in st.session_state:
    st.session_state["use_demo"] = True


st.title("📦 DemandPilot AI")
st.caption(
    "Intelligent Demand Forecasting & Inventory Optimization"
)

with st.sidebar:
    st.markdown("## 🧭 Navigation")

    current_page = st.session_state["page"]

    selected_page = st.radio(
        "Dashboard",
        PAGES,
        index=PAGES.index(current_page),
    )

    if selected_page != st.session_state["page"]:
        st.session_state["page"] = selected_page
        st.session_state["launched"] = (
            selected_page != "Home"
        )
        st.rerun()

    st.divider()

    st.markdown("### 📁 Data source")

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=["csv", "xlsx", "xls"],
        help=(
            "Required fields for forecasting: date, "
            "product ID, and units sold."
        ),
    )

    use_demo = st.checkbox(
        "Use bundled demo dataset",
        value=st.session_state["use_demo"],
        help="Used when no uploaded file is selected.",
    )

    st.session_state["use_demo"] = use_demo

    st.divider()

    st.caption("Project status")
    st.caption("Week 1–3 analytics modules retained")


# ============================================================
# 8. LANDING PAGE DISPLAY
# ============================================================

# Show the landing page until the user launches analytics.
# If a file is uploaded while on Home, allow the user to
# continue into the data configuration screen.
if (
    st.session_state["page"] == "Home"
    and not st.session_state["launched"]
    and uploaded_file is None
):
    render_landing_page()
    st.stop()


# ============================================================
# 9. LOAD THE SELECTED DATA SOURCE
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
# 10. OPTIONAL AUTO MAPPING AND MANUAL MAPPING
# ============================================================

st.subheader("1. Configure your data")

st.caption(
    "Choose whether to enable Auto Mapping after uploading. "
    "You can review and change every suggested mapping."
)

if uploaded_file is not None:
    # Each uploaded filename has its own toggle state.
    # New filenames start with Auto Mapping disabled.
    upload_key = (
        str(uploaded_file.name)
        .replace(".", "_")
        .replace(" ", "_")
    )

    auto_mapping_enabled = st.toggle(
        "✨ Enable Auto Mapping",
        value=False,
        key=f"auto_mapping_{upload_key}",
        help=(
            "OFF: select columns manually. "
            "ON: suggest matches based on column names."
        ),
    )

    if auto_mapping_enabled:
        st.success(
            "Auto Mapping is ON. Review the suggested columns below."
        )
    else:
        st.info(
            "Auto Mapping is OFF. Select the source columns manually."
        )

else:
    # The included demo dataset has known column names.
    auto_mapping_enabled = True

    st.info(
        "Demo mode uses automatic matching for the bundled dataset. "
        "Upload your own file to control the Auto Mapping toggle."
    )


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

    st.caption("* Required for demand forecasting.")


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
# 11. VALIDATE AND PREPARE THE WORKING DATA
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


# ============================================================
# 12. DEMAND OVERVIEW DASHBOARD
# ============================================================

if st.session_state["page"] == "Demand Overview":
    st.header("📈 Demand Overview")

    st.write(
        "Explore historical demand by product and identify "
        "patterns in your available data."
    )

    products = sorted(
        clean_data["product_id"].astype(str).unique().tolist()
    )

    selected_products = st.multiselect(
        "Filter products",
        products,
        default=products,
    )

    view = clean_data[
        clean_data["product_id"].astype(str).isin(selected_products)
    ].copy()

    if view.empty:
        st.warning("Select at least one product.")
        st.stop()

    total_demand = view["units_sold"].sum()

    daily_totals = view.groupby(
        "date", as_index=False
    )["units_sold"].sum()

    average_daily_demand = daily_totals["units_sold"].mean()

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Total demand",
        f"{total_demand:,.0f} units",
    )

    m2.metric(
        "Products",
        f"{view['product_id'].nunique():,}",
    )

    m3.metric(
        "Average daily demand",
        f"{average_daily_demand:,.1f}",
    )

    m4.metric(
        "Valid daily records",
        f"{len(view):,}",
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Daily demand trend")

        st.plotly_chart(
            px.line(
                daily_totals,
                x="date",
                y="units_sold",
                markers=True,
                title="Total daily demand",
                labels={
                    "date": "Date",
                    "units_sold": "Units sold",
                },
                template="plotly_dark",
            ),
            width="stretch",
        )

    with right:
        st.subheader("Demand by product")

        product_totals = view.groupby(
            "product_id", as_index=False
        )["units_sold"].sum()

        st.plotly_chart(
            px.bar(
                product_totals,
                x="product_id",
                y="units_sold",
                title="Total units by product",
                labels={
                    "product_id": "Product",
                    "units_sold": "Units sold",
                },
                template="plotly_dark",
            ),
            width="stretch",
        )

    st.subheader("Historical data preview")

    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "⬇️ Download cleaned demand CSV",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_demand_data.csv",
        mime="text/csv",
    )


# ============================================================
# 13. DATA QUALITY AND INSIGHTS
# ============================================================

elif st.session_state["page"] == "Data Quality & Insights":
    st.header("🔍 Data Quality & Insights")

    st.write(
        "Review data-quality checks before using the dataset "
        "for forecasting or inventory calculations."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Uploaded rows", f"{len(raw_data):,}")
    c2.metric("Mapped rows", f"{len(mapped_data):,}")
    c3.metric(
        "Cleaned rows",
        f"{len(clean_data):,}",
    )

    st.divider()

    st.subheader("Validation results")

    st.dataframe(
        quality,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Cleaned demand data")

    st.dataframe(
        clean_data,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "⬇️ Download cleaned data",
        data=clean_data.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_demand_data.csv",
        mime="text/csv",
    )

    st.download_button(
        "⬇️ Download quality report",
        data=quality.to_csv(index=False).encode("utf-8"),
        file_name="data_quality_report.csv",
        mime="text/csv",
    )


# ============================================================
# 14. OTHER DASHBOARD PAGES
# ============================================================

elif st.session_state["page"] == "Demand Forecasting":
    st.header("📊 Demand Forecasting")

    st.info(
        "This page is ready for integration with your existing "
        "src/forecasting.py and src/predict_future_demand.py modules. "
        "The forecasting results will be connected in the next step."
    )

    st.subheader("Available historical data")
    st.dataframe(
        clean_data.head(50),
        width="stretch",
        hide_index=True,
    )


elif st.session_state["page"] == "Inventory Intelligence":
    st.header("📦 Inventory Intelligence")

    st.info(
        "Your existing inventory calculations will be connected "
        "here. Recommendations require inventory inputs such as "
        "current stock and lead time. Demo inventory inputs must "
        "be treated as examples."
    )

    st.subheader("Available products")
    st.dataframe(
        pd.DataFrame({
            "product_id": sorted(
                clean_data["product_id"].astype(str).unique()
            )
        }),
        width="stretch",
        hide_index=True,
    )


elif st.session_state["page"] == "Model Performance":
    st.header("🎯 Model Performance")

    st.info(
        "This page will display the actual evaluation results "
        "generated by your existing model-comparison module."
    )

    st.caption(
        "Metrics will be calculated from evaluation results; "
        "no model performance scores are fabricated."
    )


elif st.session_state["page"] == "Home":
    st.header("Welcome to DemandPilot AI")

    st.write(
        "Your dataset is loaded. Choose a dashboard page "
        "from the sidebar to continue."
    )

    st.dataframe(
        clean_data.head(20),
        width="stretch",
        hide_index=True,
    )
from chatbot import render_demandpilot_chatbot

render_demandpilot_chatbot()
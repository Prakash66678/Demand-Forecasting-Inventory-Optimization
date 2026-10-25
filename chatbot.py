
import re
import time

import pandas as pd
import streamlit as st
from google import genai
from google.genai import errors

MODEL_NAME = "gemini-3.5-flash-lite"
MAX_RETRIES = 3


def build_dataset_context(question, data):
    """Build a compact, data-grounded context for the AI."""

    if data is None or data.empty:
        return "No dataset is currently available."

    df = data.copy()
    lines = [
        "CURRENT DASHBOARD DATASET",
        f"Rows: {len(df)}",
        f"Columns: {', '.join(map(str, df.columns))}",
    ]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        valid_dates = df["date"].dropna()

        if not valid_dates.empty:
            lines.append(
                f"Date range: {valid_dates.min().date()} "
                f"to {valid_dates.max().date()}"
            )

    if "units_sold" in df.columns:
        demand = pd.to_numeric(df["units_sold"], errors="coerce")
        lines.append(f"Total demand: {demand.sum():,.2f} units")
        lines.append(f"Average row demand: {demand.mean():,.2f} units")

    if "product_id" in df.columns:
        lines.append(
            f"Number of products: {df['product_id'].nunique()}"
        )

        top_products = (
            df.groupby("product_id")["units_sold"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        lines.append("Top products by total demand:")
        lines.append(top_products.to_string())

    # If the question contains a date, include records for that date.
    date_match = re.search(
        r"\b\d{4}-\d{2}-\d{2}\b", question
    )

    if date_match and "date" in df.columns:
        requested_date = pd.to_datetime(
            date_match.group(), errors="coerce"
        )

        if pd.notna(requested_date):
            matching = df[
                df["date"].dt.date == requested_date.date()
            ]
            lines.append(
                f"\nRecords for {requested_date.date()}:"
            )

            if matching.empty:
                lines.append("No records found for this date.")
            else:
                lines.append(
                    matching.head(100).to_csv(index=False)
                )

    # Include monthly demand totals when the question asks about months.
    if (
        "date" in df.columns
        and "units_sold" in df.columns
        and any(word in question.lower() for word in [
            "month", "monthly", "trend", "over time"
        ])
    ):
        monthly = (
            df.dropna(subset=["date"])
            .assign(month=lambda x: x["date"].dt.to_period("M").astype(str))
            .groupby("month", as_index=False)["units_sold"]
            .sum()
        )
        lines.append("\nMonthly demand totals:")
        lines.append(monthly.tail(36).to_csv(index=False))

    # Include records for a product explicitly mentioned in the question.
    if "product_id" in df.columns:
        product_ids = df["product_id"].astype(str).unique()
        question_lower = question.lower()

        matched_products = [
            product for product in product_ids
            if str(product).lower() in question_lower
        ]

        if matched_products:
            product_rows = df[
                df["product_id"].astype(str).isin(matched_products)
            ]
            lines.append("\nRecords for the requested product:")
            lines.append(product_rows.tail(50).to_csv(index=False))

    # A small sample helps answer general questions without sending
    # the entire dataset to the API.
    lines.append("\nRecent cleaned dataset rows:")
    lines.append(df.tail(15).to_csv(index=False))

    return "\n".join(lines)


def get_ai_response(question, history, data):
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Check Streamlit Secrets."
        )

    client = genai.Client(api_key=api_key)
    dataset_context = build_dataset_context(question, data)

    instructions = """
You are DemandPilot AI Assistant for demand forecasting
and inventory optimization.

Use simple English and beginner-friendly explanations.

IMPORTANT RULES:
1. Answer questions using the supplied CURRENT DASHBOARD DATASET.
2. Never invent demand, dates, product values, inventory, or forecasts.
3. If the supplied data does not contain the answer, say so clearly.
4. For exact numbers, use the provided data records and summaries.
5. Distinguish actual historical demand from predicted demand.
6. The dataset may contain only date, product_id, and units_sold.
   Do not claim inventory or forecast results exist unless provided.
7. If a date has no matching records, say no matching records were found.
8. Treat the dataset as the currently selected and cleaned dashboard data.
"""

    conversation = []

    for message in history[-6:]:
        role = "User" if message["role"] == "user" else "Assistant"
        conversation.append(f"{role}: {message['content']}")

    prompt = (
        instructions
        + "\n\n"
        + dataset_context
        + "\n\nCONVERSATION:\n"
        + "\n".join(conversation)
        + f"\nUser's current question: {question}"
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty response.")

            return response.text

        except errors.APIError as error:
            status_code = getattr(error, "code", None)

            if status_code in (429, 500, 503):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue

                if status_code == 503:
                    raise RuntimeError(
                        "Gemini is temporarily overloaded. "
                        "Please try again shortly."
                    ) from error

                if status_code == 429:
                    raise RuntimeError(
                        "Gemini API quota or rate limit reached."
                    ) from error

            if status_code in (401, 403):
                raise RuntimeError(
                    "Gemini authentication failed. Check your API key."
                ) from error

            raise RuntimeError(
                f"Gemini API request failed (HTTP {status_code})."
            ) from error

    raise RuntimeError("Gemini could not respond. Please try again.")


def render_demandpilot_chatbot(data):
    st.subheader("🤖 DemandPilot AI Assistant")
    st.caption(
        "Ask questions about the currently loaded dataset, "
        "demand trends, and products."
    )

    if "demandpilot_chat_history" not in st.session_state:
        st.session_state.demandpilot_chat_history = []

    if st.button("Clear chat", key="demandpilot_clear_chat"):
        st.session_state.demandpilot_chat_history = []
        st.rerun()

    for message in st.session_state.demandpilot_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask about a date, product, or demand trend...",
        key="demandpilot_chat_input",
    )

    if question:
        st.session_state.demandpilot_chat_history.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your dataset..."):
                try:
                    answer = get_ai_response(
                        question,
                        st.session_state.demandpilot_chat_history[:-1],
                        data,
                    )
                    st.markdown(answer)
                    st.session_state.demandpilot_chat_history.append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as error:
                    st.error(str(error))

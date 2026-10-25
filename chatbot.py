
import streamlit as st
from google import genai

MODEL_NAME = "gemini-3.1-flash-lite"


def get_ai_response(question, history):
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Check .streamlit/secrets.toml."
        )

    client = genai.Client(api_key=api_key)

    instructions = """
You are DemandPilot AI Assistant, helping users understand
demand forecasting and inventory optimization.

Use simple English. Explain:
- Demand forecasting
- Moving averages and forecasting methods
- Safety stock and reorder points
- Inventory optimization and stockout risk

Do not invent actual project sales figures, forecasts,
inventory values, or dashboard results.
You cannot access live dashboard data unless it is provided.
"""

    conversation = []

    for message in history[-8:]:
        role = "User" if message["role"] == "user" else "Assistant"
        conversation.append(f"{role}: {message['content']}")

    conversation.append(f"User: {question}")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=instructions + "\n\n" + "\n".join(conversation),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text


def render_demandpilot_chatbot():
    st.subheader("🤖 DemandPilot AI Assistant")
    st.caption(
        "Ask questions about demand forecasting and inventory optimization."
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
        "Ask about forecasting, safety stock or reorder points...",
        key="demandpilot_chat_input",
    )

    if question:
        st.session_state.demandpilot_chat_history.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("DemandPilot AI is thinking..."):
                try:
                    answer = get_ai_response(
                        question,
                        st.session_state.demandpilot_chat_history[:-1],
                    )

                    st.markdown(answer)

                    st.session_state.demandpilot_chat_history.append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as error:
                    st.error("The chatbot could not generate a response.")
                    st.caption(f"Technical details: {error}")

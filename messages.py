import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st

MESSAGES_FILE = Path("./messages/messages.json")


def show_messages(category):

    st.title(f"💬 {category} Messages")

    # -----------------------------
    # Back button
    # -----------------------------

    if st.button("⬅ Back to Menu", width="content"):
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    if "editing_message" not in st.session_state:
        st.session_state.editing_message = None

    # -----------------------------
    # Current dates
    # -----------------------------

    current_date = datetime.today()
    today_day = current_date.isoweekday()

    days_until_sat = (5 - current_date.weekday()) % 7
    if days_until_sat == 0:
        days_until_sat = 7

    next_saturday = current_date + timedelta(days=days_until_sat)
    next_sunday = next_saturday + timedelta(days=1)

    # -----------------------------
    # Load JSON
    # -----------------------------

    with open(MESSAGES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    messages = data["messages"]

    # -----------------------------
    # Filter category
    # -----------------------------

    filtered = [
        m
        for m in messages
        if m["category"] == category
    ]

    if not filtered:
        st.info("No messages available.")
        return

    # -----------------------------
    # Sort
    # -----------------------------

    def sort_key(msg):

        day = msg.get("day")

        if day is None:
            return (999, msg.get("order", 999))

        return (
            (day - today_day) % 7,
            msg.get("order", 999),
        )

    filtered.sort(key=sort_key)

    # -----------------------------
    # Display
    # -----------------------------

    for msg in filtered:

        formatted_text = (
            msg["text"]
            .replace("{TODAY}", current_date.strftime("%m/%d"))
            .replace(
                "{TOMORROW}",
                (current_date + timedelta(days=1)).strftime("%m/%d"),
            )
            .replace(
                "{NEXT_SATURDAY}",
                next_saturday.strftime("%m/%d"),
            )
            .replace(
                "{NEXT_SUNDAY}",
                next_sunday.strftime("%m/%d"),
            )
        )

        with st.container(border=True):

            # ------------------------
            # Header
            # ------------------------

            c1, c2 = st.columns([5, 1])

            with c1:

                st.subheader(msg["title"])

                if msg.get("day") == today_day:
                    st.success("🟢 Today's Message")

            with c2:

                if st.session_state.editing_message != msg["id"]:

                    if st.button(
                        "✏️ Edit",
                        key=f"edit_{msg['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.editing_message = msg["id"]
                        st.rerun()

            # ------------------------
            # Edit mode
            # ------------------------

            if st.session_state.editing_message == msg["id"]:

                edited = st.text_area(
                    "Message",
                    value=msg["text"],
                    key=f"text_{msg['id']}",
                    height=250,
                    label_visibility="collapsed",
                )

                save_col, cancel_col = st.columns(2)

                with save_col:

                    if st.button(
                        "💾 Save",
                        key=f"save_{msg['id']}",
                        use_container_width=True,
                    ):

                        msg["text"] = edited

                        with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
                            json.dump(
                                data,
                                f,
                                indent=2,
                                ensure_ascii=False,
                            )

                        st.session_state.editing_message = None
                        st.success("Message saved!")
                        st.rerun()

                with cancel_col:

                    if st.button(
                        "❌ Cancel",
                        key=f"cancel_{msg['id']}",
                        use_container_width=True,
                    ):

                        st.session_state.editing_message = None
                        st.rerun()

            # ------------------------
            # View mode
            # ------------------------

            else:

                st.code(
                    formatted_text,
                    language=None,
                )
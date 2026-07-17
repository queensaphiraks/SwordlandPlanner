import streamlit as st


def show_home():

    # st.title("🏰 KNG TOOLKIT")
    st.markdown(
    """
    <h1 style="text-align: center;">
        🏰 KNG TOOLKIT
    </h1>
    """,
    unsafe_allow_html=True,
)

    # Swordland
    st.header("⚔️ Swordland Planner")

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "➕ Create Plan",
            use_container_width=True,
            key="sl_create",
        ):
            st.session_state.page = "swordland_create"
            st.rerun()

    with c2:
        if st.button(
            "📂 Load Plan",
            use_container_width=True,
            key="sl_load",
        ):
            st.session_state.page = "swordland_load"
            st.rerun()

    st.divider()

    # Tri Alliance
    st.header("🤝 Tri-Alliance Planner")

    c1, c2 = st.columns(2)

    with c1:
        st.button(
            "➕ Create Plan",
            use_container_width=True,
            key="ta_create",
        )

    with c2:
        st.button(
            "📂 Load Plan",
            use_container_width=True,
            key="ta_load",
        )

    st.divider()

    # Messages
    st.header("💬 Kingshot Messages")

    buttons = [
        "KVK",
        "Alliance Brawl",
        "Golden Glaives",
        "Bear",
        "Vikings",
        "Alliance Championship",
        "Caesar's Bosses",
        "Swordland",
        "Various",
    ]

    MESSAGE_CATEGORIES = [
    ("🛡️ KVK", "KVK"),
    ("🏹 Alliance Brawl", "Alliance Brawl"),
    ("🗡️ Golden Glaives", "Golden Glaives"),
    ("🐻 Bear", "Bear"),
    ("🪓 Vikings", "Vikings"),
    ("🏆 Alliance Championship", "AC"),
    ("⚜️ Cesares Fury", "Cesares Fury"),
    ("⚔️ Swordland & Tri", "Swordland & Tri"),
    ("📋 Various", "Various"),
    ]

    for i in range(0, len(MESSAGE_CATEGORIES), 2):

        cols = st.columns(2)

        for col, (label, category) in zip(cols, MESSAGE_CATEGORIES[i:i+2]):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=f"msg_{category}",
                ):
                    st.session_state.page = "messages"
                    st.session_state.message_category = category
                    st.rerun()
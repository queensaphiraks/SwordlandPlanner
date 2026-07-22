import streamlit as st

from home import show_home
from swordland import show_swordland
from tri import show_tri
from messages import show_messages

st.set_page_config(
    page_title="KNG Toolkit",
    page_icon="🏰",
    layout="centered",
)

if "page" not in st.session_state:
    st.session_state.page = "home"

page = st.session_state.page

if page == "home":
    show_home()

elif page in ["swordland_create", "swordland_load"]:
    show_swordland(page)

elif page in ["tri_create", "tri_load"]:
    show_tri(page)

elif page == "messages":

    show_messages(
        st.session_state.message_category
    )
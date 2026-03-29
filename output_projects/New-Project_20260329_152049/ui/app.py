import streamlit as st
from streamlit_option_menu import option_menu
from ui.pages import dashboard, kanban, ticket_form, analytics
from ui.components.navbar import render_navbar
from config.settings import Settings

def render():
    """Streamlit 多頁路由主程式"""
    st.set_page_config(
        page_title="AI-CSM",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    settings = Settings()

    # 全域導覽列
    render_navbar()

    # 依據網址參數決定頁面
    query_params = st.query_params
    page = query_params.get("page", ["dashboard"])[0]

    if page == "dashboard":
        dashboard.render()
    elif page == "kanban":
        kanban.render()
    elif page == "ticket_form":
        ticket_form.render()
    elif page == "analytics":
        analytics.render()
    else:
        st.error("未知頁面，將導向儀表板...")
        st.query_params.update({"page": "dashboard"})
        st.rerun()
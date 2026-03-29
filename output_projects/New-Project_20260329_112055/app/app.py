import streamlit as st
from app import config, db, auth
from app.pages import dashboard, case_create, case_detail, kanban, reports
from app.models.user import User
from pathlib import Path
import os

# ---------- 全域相依注入 ----------
def _inject_global_deps():
    """在 Streamlit 每次 Script Run 時注入全域物件"""
    # 1. 設定
    st.session_state["settings"] = config.get_settings()
    # 2. 資料庫初始化（僅第一次）
    if "db_initialized" not in st.session_state:
        schema_path = Path(__file__).with_name("schema.sql")
        if schema_path.exists():
            with open(schema_path, encoding="utf-8") as f:
                db.init_db(f.read())
        st.session_state["db_initialized"] = True

# ---------- 路由表 ----------
_PAGES = {
    "dashboard": {"func": dashboard.show, "name": "儀表板", "icon": "📊"},
    "case_create": {"func": case_create.show, "name": "建立案件", "icon": "➕"},
    "kanban": {"func": kanban.show, "name": "Kanban 看板", "icon": "📋"},
    "reports": {"func": reports.show, "name": "報表", "icon": "📈"},
}

# ---------- 側邊欄導航 ----------
def _render_sidebar():
    with st.sidebar:
        # Logo
        logo_path = Path(__file__).parent / "static" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), use_column_width=True)
        else:
            st.title("AICMS")

        # 用戶資訊 & 登出
        user: User = st.session_state.get("user")
        if user:
            st.write(f"歡迎，{user.name} ({user.email})")
            if st.button("登出"):
                auth.logout()
                st.rerun()
        else:
            st.info("請先登入")

        st.divider()

        # 頁面選單
        selection = st.radio(
            "導航",
            options=list(_PAGES.keys()),
            format_func=lambda k: f"{_PAGES[k]['icon']} {_PAGES[k]['name']}",
            key="nav_radio",
        )
        return selection

# ---------- 登入頁 ----------
def _render_login():
    st.title("AI 客服案件管理系統")
    st.markdown("### 請使用 Azure AD 登入")
    if st.button("登入", type="primary"):
        user_info = auth.login()
        if user_info:
            st.session_state["user"] = user_info
            st.rerun()
        else:
            st.error("登入失敗，請聯絡管理員")

# ---------- 主程式 ----------
def run():
    """Streamlit 多頁路由與全域相依注入；公開：run() -> None"""
    st.set_page_config(
        page_title="AICMS",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 全域相依注入
    _inject_global_deps()

    # 樣式
    css_path = Path(__file__).parent / "static" / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # 登入檢查
    if "user" not in st.session_state:
        _render_login()
        return

    # 側邊欄導航
    selected_page = _render_sidebar()

    # 根據路由執行頁面
    page_config = _PAGES.get(selected_page)
    if page_config:
        st.markdown(f"## {page_config['name']}")
        # 動態載入對應頁面
        page_config["func"]()

    # 特殊路由：case_detail 需帶參數
    query_params = st.query_params.to_dict()
    if "case_id" in query_params:
        case_id = query_params["case_id"]
        st.markdown("---")
        case_detail.show(case_id)

# ---------- 直接執行 ----------
if __name__ == "__main__":
    run()
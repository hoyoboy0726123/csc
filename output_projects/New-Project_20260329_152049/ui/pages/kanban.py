import streamlit as st
from models.ticket import Ticket
from models.user import User
from ui.components.ticket_card import ticket_card
from ui.components.navbar import navbar
import logging

logger = logging.getLogger(__name__)

def render():
    navbar()
    st.title("Kanban 看板")

    # 取得篩選條件
    col1, col2 = st.columns([1, 3])
    with col1:
        assignee_filter = st.selectbox("篩選負責人", ["全部"] + [u.name for u in User.list_all()])
    with col2:
        search = st.text_input("搜尋標題", "")

    # 依狀態分組
    statuses = ["待處理", "處理中", "已解決"]
    kanban = {s: [] for s in statuses}
    tickets = Ticket.list_by_status()
    for t in tickets:
        # 負責人篩選
        if assignee_filter != "全部":
            user = next((u for u in User.list_all() if u.id == t.assignee_id), None)
            if not user or user.name != assignee_filter:
                continue
        # 標題搜尋
        if search and search.lower() not in t.title.lower():
            continue
        kanban[t.status].append(t)

    # 三欄排版
    cols = st.columns(3)
    for idx, status in enumerate(statuses):
        with cols[idx]:
            st.subheader(f"{status} ({len(kanban[status])})")
            container = st.container()
            with container:
                for t in kanban[status]:
                    # 顯示卡片
                    ticket_card(t)

    # 自動重新載入
    if st.button("🔄 重新整理"):
        st.rerun()
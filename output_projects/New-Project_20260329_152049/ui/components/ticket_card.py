import streamlit as st
from datetime import datetime
from models.ticket import Ticket
from models.user import User
from services.llm_service import LLMService
from services.outlook_service import OutlookService
from services.notification_service import NotificationService
from ui.pages.ticket_form import show_ticket_form

def render_card(ticket: Ticket):
    """
    在 Streamlit 上渲染一張 Ticket 卡片，提供編輯、指派、AI 草稿、狀態切換等功能。
    依賴：Streamlit、models.ticket.Ticket、models.user.User
    """
    # 卡片容器
    with st.container():
        col_main, col_actions = st.columns([3, 1])
        with col_main:
            st.markdown(f"**{ticket.title}**")
            st.caption(f"建立於 {ticket.created_at}")
            status_color = {
                "待處理": "🔴",
                "處理中": "🟡",
                "已解決": "🟢"
            }.get(ticket.status, "⚪")
            st.write(f"{status_color} 狀態：{ticket.status}")
            if ticket.assignee_id:
                assignee = User.get_by_id(ticket.assignee_id)
                st.write(f"👤 負責人：{assignee.name if assignee else '未知'}")
            else:
                st.write("👤 尚未指派")

        with col_actions:
            # 編輯按鈕
            if st.button("✏️ 編輯", key=f"edit_{ticket.id}"):
                st.session_state[f"edit_mode_{ticket.id}"] = True
            # AI 草稿按鈕
            if st.button("🤖 草稿", key=f"draft_{ticket.id}"):
                with st.spinner("AI 生成回覆中..."):
                    llm = LLMService()
                    draft = llm.generate_reply(ticket)
                    st.session_state[f"draft_{ticket.id}"] = draft
            # Outlook 草稿按鈕
            if st.button("📤 Outlook", key=f"outlook_{ticket.id}"):
                outlook = OutlookService()
                draft_body = st.session_state.get(f"draft_{ticket.id}", "")
                outlook.create_draft(ticket.title, draft_body)
                st.success("已建立 Outlook 草稿")

        # 編輯模式展開表單
        if st.session_state.get(f"edit_mode_{ticket.id}", False):
            show_ticket_form(ticket)

        # 顯示 AI 草稿
        draft_key = f"draft_{ticket.id}"
        if draft_key in st.session_state:
            st.text_area("AI 回覆草稿", value=st.session_state[draft_key], height=200)

        # 狀態切換（Kanban 拖曳模擬）
        st.write("---")
        new_status = st.selectbox(
            "變更狀態",
            ["待處理", "處理中", "已解決"],
            index=["待處理", "處理中", "已解決"].index(ticket.status),
            key=f"status_{ticket.id}"
        )
        if new_status != ticket.status:
            # 未指派不可進入「處理中」
            if new_status == "處理中" and not ticket.assignee_id:
                st.error("請先指派負責人！")
            else:
                ticket.status = new_status
                ticket.save()
                st.rerun()

        # 負責人指派
        users = User.list_all()
        assignee_options = [u for u in users if u.role == "agent"] + [u for u in users if u.role == "manager"]
        current_index = 0
        if ticket.assignee_id:
            current_index = next((i for i, u in enumerate(assignee_options) if u.id == ticket.assignee_id), 0)
        new_assignee = st.selectbox(
            "指派給",
            options=assignee_options,
            format_func=lambda u: u.name,
            index=current_index,
            key=f"assignee_{ticket.id}"
        )
        if new_assignee and new_assignee.id != ticket.assignee_id:
            ticket.assignee_id = new_assignee.id
            ticket.save()
            NotificationService().notify_assign(new_assignee.email, ticket)
            st.success(f"已指派給 {new_assignee.name}")
            st.rerun()
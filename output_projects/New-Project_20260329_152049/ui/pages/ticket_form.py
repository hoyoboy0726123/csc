import streamlit as st
from datetime import datetime
from models.ticket import Ticket
from models.user import User
from services.llm_service import LLMService
from services.pdf_parser import PDFParser
from services.email_parser import EmailParser
import os
import uuid

def render(ticket_id: int = None):
    st.title("新增 / 編輯案件")

    # 載入所有使用者供指派
    users = User.list_all()
    user_options = {f"{u.name} ({u.email})": u.id for u in users}

    # 初始化表單值
    if ticket_id:
        ticket = Ticket.get_by_id(ticket_id)
        if not ticket:
            st.error("案件不存在")
            return
        title = st.text_input("主旨", value=ticket.title)
        description = st.text_area("描述", value=ticket.description or "")
        status = st.selectbox("狀態", ["待處理", "處理中", "已解決"], index=["待處理", "處理中", "已解決"].index(ticket.status))
        assignee_id = st.selectbox(
            "指派給",
            options=list(user_options.keys()),
            index=list(user_options.values()).index(ticket.assignee_id) if ticket.assignee_id else 0
        )
        due_date = st.date_input("建議結案日", value=datetime.strptime(ticket.due_date, "%Y-%m-%d") if ticket.due_date else datetime.today())
    else:
        title = st.text_input("主旨", value="")
        description = st.text_area("描述", value="")
        status = st.selectbox("狀態", ["待處理", "處理中", "已解決"])
        assignee_id = st.selectbox("指派給", options=list(user_options.keys()))
        due_date = st.date_input("建議結案日", value=datetime.today())

    # 檔案上傳區
    st.subheader("自動帶入資料（選填）")
    input_type = st.radio("輸入方式", ["手動", "上傳 PDF", "貼上 Email 原文"])
    if input_type == "上傳 PDF":
        uploaded = st.file_uploader("選擇 PDF", type=["pdf"])
        if uploaded and st.button("解析 PDF"):
            with st.spinner("解析中..."):
                parser = PDFParser()
                text = parser.extract_text(uploaded)
                llm = LLMService()
                data = llm.extract_fields(text)
                title = st.text_input("主旨", value=data.get("title", title))
                description = st.text_area("描述", value=data.get("description", description))
                if data.get("due_date"):
                    due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
    elif input_type == "貼上 Email 原文":
        email_raw = st.text_area("Email 原文")
        if email_raw and st.button("解析 Email"):
            with st.spinner("解析中..."):
                parser = EmailParser()
                text = parser.parse(email_raw)
                llm = LLMService()
                data = llm.extract_fields(text)
                title = st.text_input("主旨", value=data.get("title", title))
                description = st.text_area("描述", value=data.get("description", description))
                if data.get("due_date"):
                    due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")

    # 儲存按鈕
    if st.button("儲存"):
        if not title.strip():
            st.error("主旨不可空白")
            return
        assignee = user_options[assignee_id]
        if ticket_id:
            ticket.title = title
            ticket.description = description
            ticket.status = status
            ticket.assignee_id = assignee
            ticket.due_date = due_date.strftime("%Y-%m-%d")
            ticket.save()
            st.success("案件已更新")
        else:
            ticket = Ticket(
                id=None,
                title=title,
                description=description,
                status=status,
                assignee_id=assignee,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                due_date=due_date.strftime("%Y-%m-%d")
            )
            ticket.save()
            st.success("案件已建立")
        st.rerun()
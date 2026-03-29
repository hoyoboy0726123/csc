import streamlit as st
from models.case import get_case, update_case
from components.kanban import render_kanban
from services.ai_service import generate_reply_draft
from services.outlook_service import send_email

def case_detail_page(case_id):
    case = get_case(case_id)
    if case is None:
        st.error("Case not found")
        return

    st.header(f"Case {case_id} - {case.client_name}")
    st.write(f"Product Number: {case.product_number}")
    st.write(f"Summary: {case.summary}")
    st.write(f"Suggested Close Date: {case.suggested_close_date}")
    st.write(f"Status: {case.status}")
    st.write(f"Assignee: {case.assignee}")

    # Render Kanban
    render_kanban(case_id)

    # AI 生成回覆草稿
    if st.button("Generate Reply Draft"):
        draft = generate_reply_draft(case_id)
        st.write(f"Reply Draft: {draft}")

    # 一鍵導入 Outlook 草稿匣
    if st.button("Send to Outlook"):
        send_email(case_id, "recipient@example.com", "Test Email", "Test Body")

    # 更新案件狀態
    new_status = st.selectbox("Update Status", ["待處理", "處理中", "已解決"], case.status)
    if st.button("Update Status"):
        update_case(case_id, status=new_status)

if __name__ == "__main__":
    case_id = st.query_params.get("case_id", 0)
    case_detail_page(int(case_id))
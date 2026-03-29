import streamlit as st
from models.case import Case
from components.case_table import CaseTable
from services.ai_service import AIService
from utils.data_utils import connect_to_db, execute_query

def main():
    st.title("案件智能管理系統（CaseIntelli）")
    st.sidebar.title("案件列表")

    # 連接資料庫
    db_connection = connect_to_db()

    # 查詢案件列表
    query = "SELECT * FROM cases"
    cases = execute_query(query, (), db_connection)

    # 渲染案件表格
    case_table = CaseTable(cases)
    case_table.render()

    # 新增案件
    with st.sidebar.form("新增案件"):
        client_name = st.text_input("客戶名稱")
        product_number = st.text_input("產品編號")
        summary = st.text_input("案件摘要")
        suggested_close_date = st.date_input("建議結案日期")
        assignee = st.selectbox("負責人", [1, 2, 3])  # 假設負責人 ID 為 1, 2, 3
        submitted = st.form_submit_button("新增案件")

        if submitted:
            # 新增案件到資料庫
            case = Case(
                client_name=client_name,
                product_number=product_number,
                summary=summary,
                suggested_close_date=suggested_close_date,
                assignee=assignee
            )
            case.save()

            # 自動結構化案件數據
            AIService.extract_info_from_text(case.summary)

    # 自動生成回覆草稿
    with st.sidebar.form("自動生成回覆草稿"):
        case_id = st.selectbox("選擇案件", [1, 2, 3])  # 假設案件 ID 為 1, 2, 3
        submitted = st.form_submit_button("生成回覆草稿")

        if submitted:
            # 生成回覆草稿
            draft = AIService.generate_reply_draft(case_id)
            st.write(draft)

if __name__ == "__main__":
    main()
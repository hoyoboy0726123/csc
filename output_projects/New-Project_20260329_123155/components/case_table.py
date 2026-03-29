import streamlit as st
import pandas as pd
from models.case import Case
from utils.data_utils import connect_to_db, execute_query

def get_cases():
    db_connection = connect_to_db()
    query = "SELECT * FROM cases"
    cases_data = execute_query(db_connection, query, ())
    cases = []
    for case_data in cases_data:
        case = Case(**case_data)
        cases.append(case)
    return cases

def get_assignees():
    db_connection = connect_to_db()
    query = "SELECT * FROM assignees"
    assignees_data = execute_query(db_connection, query, ())
    assignees = []
    for assignee_data in assignees_data:
        assignee = {"id": assignee_data[0], "name": assignee_data[1]}
        assignees.append(assignee)
    return assignees

def case_table():
    st.title("案件列表")
    cases = get_cases()
    assignees = get_assignees()
    assignee_dict = {assignee["id"]: assignee["name"] for assignee in assignees}
    
    data = []
    for case in cases:
        data.append({
            "案件 ID": case.id,
            "客戶名稱": case.client_name,
            "產品編號": case.product_number,
            "案件摘要": case.summary,
            "建議結案日期": case.suggested_close_date,
            "案件狀態": case.status,
            "負責人": assignee_dict.get(case.assignee, "未指派")
        })
    
    df = pd.DataFrame(data)
    st.write(df)

    # 新增篩選功能
    status_filter = st.selectbox("案件狀態", options=["全部", "待處理", "處理中", "已解決"], index=0)
    if status_filter != "全部":
        df_filtered = df[df["案件狀態"] == status_filter]
        st.write(df_filtered)
    else:
        st.write(df)

case_table()
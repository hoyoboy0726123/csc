import streamlit as st
from models.case import Case
from models.assignee import Assignee
from services.ai_service import AIService
from services.outlook_service import OutlookService
from utils.data_utils import connect_to_db, execute_query
from utils.llm_utils import get_llm_response
from components.kanban import Kanban
from components.case_table import CaseTable
from components.assignee_table import AssigneeTable

def get_cases():
    db = connect_to_db()
    query = "SELECT * FROM cases"
    cases = execute_query(db, query, ())
    return cases

def get_assignees():
    db = connect_to_db()
    query = "SELECT * FROM assignees"
    assignees = execute_query(db, query, ())
    return assignees

def dashboard():
    st.title("案件智能管理系統 - Dashboard")
    
    # 案件狀態統計
    cases = get_cases()
    case_status_count = {}
    for case in cases:
        status = case[5]
        if status not in case_status_count:
            case_status_count[status] = 1
        else:
            case_status_count[status] += 1
    
    # 案件負荷統計
    assignees = get_assignees()
    assignee_case_count = {}
    for assignee in assignees:
        assignee_id = assignee[0]
        query = "SELECT COUNT(*) FROM cases WHERE assignee = ?"
        count = execute_query(db, query, (assignee_id,))[0][0]
        assignee_case_count[assignee[1]] = count
    
    # 顯示統計數據
    st.header("案件狀態統計")
    st.bar_chart(case_status_count)
    
    st.header("案件負荷統計")
    st.bar_chart(assignee_case_count)
    
    # 顯示案件列表
    st.header("案件列表")
    CaseTable().render(cases)
    
    # 顯示負責人列表
    st.header("負責人列表")
    AssigneeTable().render(assignees)
    
    # 顯示 Kanban
    st.header("Kanban")
    Kanban().render(cases)

if __name__ == "__main__":
    dashboard()
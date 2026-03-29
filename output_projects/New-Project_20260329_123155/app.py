import streamlit as st
from models.case import Case
from models.assignee import Assignee
from services.ai_service import AIService
from services.outlook_service import OutlookService
from pages.case_list import CaseList
from pages.case_detail import CaseDetail
from pages.assignee_list import AssigneeList
from pages.dashboard import Dashboard

def main():
    st.title("案件智能管理系統（CaseIntelli）")

    # 初始化資料庫
    Case.connect_to_db()
    Assignee.connect_to_db()

    # 建立頁面
    pages = {
        "案件列表": CaseList(),
        "案件詳情": CaseDetail(),
        "負責人列表": AssigneeList(),
        "儀表板": Dashboard()
    }

    # 選擇頁面
    selected_page = st.selectbox("選擇頁面", list(pages.keys()))

    # 渲染頁面
    pages[selected_page].render()

if __name__ == "__main__":
    main()
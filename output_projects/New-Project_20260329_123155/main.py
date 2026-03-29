import streamlit as st
from models.case import Case
from models.assignee import Assignee
from services.ai_service import AIService
from services.outlook_service import OutlookService
from utils.data_utils import connect_to_db
from utils.llm_utils import get_llm_response
from pages.case_list import case_list_page
from pages.case_detail import case_detail_page
from pages.assignee_list import assignee_list_page
from pages.dashboard import dashboard_page

def main():
    # Connect to database
    db = connect_to_db()

    # Initialize services
    ai_service = AIService()
    outlook_service = OutlookService()

    # Initialize models
    case_model = Case(db)
    assignee_model = Assignee(db)

    # Streamlit app
    st.title("案件智能管理系統")

    pages = {
        "案件列表": case_list_page,
        "案件詳情": case_detail_page,
        "負責人列表": assignee_list_page,
        "儀表板": dashboard_page
    }

    selected_page = st.selectbox("選擇頁面", list(pages.keys()))

    if selected_page == "案件列表":
        case_list_page(case_model, ai_service)
    elif selected_page == "案件詳情":
        case_detail_page(case_model, ai_service)
    elif selected_page == "負責人列表":
        assignee_list_page(assignee_model)
    elif selected_page == "儀表板":
        dashboard_page(case_model, assignee_model)

if __name__ == "__main__":
    main()
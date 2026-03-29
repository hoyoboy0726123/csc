import streamlit as st
from models.case import Case
from models.assignee import Assignee
from utils.data_utils import connect_to_db, execute_query

# 案件看板
def kanban():
    # 連接資料庫
    conn = connect_to_db()
    
    # 查詢案件狀態
    query = "SELECT * FROM cases"
    cases = execute_query(query, conn)
    
    # 查詢負責人
    query = "SELECT * FROM assignees"
    assignees = execute_query(query, conn)
    
    # 建立看板
    st.title("案件看板")
    col1, col2, col3 = st.columns(3)
    
    # 待處理案件
    col1.write("待處理案件")
    for case in cases:
        if case['status'] == '待處理':
            col1.write(f"案件ID：{case['id']}, 客戶名稱：{case['client_name']}, 負責人：{next((a['name'] for a in assignees if a['id'] == case['assignee']), '未指派')}")
    
    # 處理中案件
    col2.write("處理中案件")
    for case in cases:
        if case['status'] == '處理中':
            col2.write(f"案件ID：{case['id']}, 客戶名稱：{case['client_name']}, 負責人：{next((a['name'] for a in assignees if a['id'] == case['assignee']), '未指派')}")
    
    # 已解決案件
    col3.write("已解決案件")
    for case in cases:
        if case['status'] == '已解決':
            col3.write(f"案件ID：{case['id']}, 客戶名稱：{case['client_name']}, 負責人：{next((a['name'] for a in assignees if a['id'] == case['assignee']), '未指派')}")
    
    # 關閉資料庫連接
    conn.close()

# 主程式
if __name__ == "__main__":
    kanban()
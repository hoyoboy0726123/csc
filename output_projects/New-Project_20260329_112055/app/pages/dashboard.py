import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from app.services.reporting_service import get_kpi
from app.auth import get_current_user
from app.db import get_conn
from app.models.case import Case

def show():
    user = get_current_user()
    if not user:
        st.warning("請先登入")
        return

    st.title("AI 客服案件管理系統 - 儀表板")
    st.write(f"歡迎，{user.name}（{user.email}）")

    # 時間範圍選擇
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("統計區間", ["日", "週", "月"], index=0)
    with col2:
        if period == "日":
            days = 1
        elif period == "週":
            days = 7
        else:
            days = 30
    kpi = get_kpi(days)

    # 關鍵指標卡片
    st.subheader("關鍵指標")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("待處理案件數", kpi.pending_count)
    with col2:
        st.metric("平均處理時長（小時）", f"{kpi.avg_handling_hours:.1f}")
    with col3:
        st.metric("逾時案件數（>24h）", kpi.overdue_count)

    # 趨勢圖（簡化版：使用表格呈現每日數據）
    st.subheader("趨勢（近30日）")
    trend_days = 30
    trend_data = []
    for d in range(trend_days):
        date = datetime.now().date() - timedelta(days=d)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT status, COUNT(*) FROM cases
            WHERE DATE(created_at) = ?
            GROUP BY status
        """, (date.isoformat(),))
        rows = cur.fetchall()
        status_map = dict(rows)
        trend_data.append({
            "日期": date.isoformat(),
            "待處理": status_map.get("To Do", 0),
            "處理中": status_map.get("In Progress", 0),
            "已解決": status_map.get("Resolved", 0),
        })
        conn.close()
    df_trend = pd.DataFrame(trend_data)
    if not df_trend.empty:
        st.line_chart(df_trend.set_index("日期"))
    else:
        st.info("暫無趨勢資料")

    # 待處理案件列表
    st.subheader("待處理案件（Top 10）")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, customer_name, product_id, summary, due_date, assignee_id
        FROM cases
        WHERE status = 'To Do'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()
    if rows:
        df = pd.DataFrame(rows, columns=["案件ID", "客戶名稱", "產品編號", "摘要", "結案日期", "指派給"])
        st.dataframe(df)
    else:
        st.success("目前無待處理案件")

    # 快速操作按鈕
    st.subheader("快速操作")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("建立新案件"):
            st.session_state["page"] = "case_create"
            st.rerun()
    with col2:
        if st.button("查看 Kanban"):
            st.session_state["page"] = "kanban"
            st.rerun()
    with col3:
        if st.button("查看報表"):
            st.session_state["page"] = "reports"
            st.rerun()
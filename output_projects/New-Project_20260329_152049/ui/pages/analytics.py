import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.analytics_service import AnalyticsService


def render():
    st.title("📊 分析報表")

    # 初始化服務
    svc = AnalyticsService()

    # 篩選器
    col1, col2, col3 = st.columns(3)
    with col1:
        days = st.selectbox("區間（天）", [7, 14, 30, 90], index=2)
    with col2:
        assignee = st.selectbox("負責人", ["全部"] + svc.get_assignee_list())
    with col3:
        status = st.selectbox("狀態", ["全部", "待處理", "處理中", "已解決"])

    # 取得資料
    df = svc.get_tickets_in_period(days, assignee=None if assignee == "全部" else assignee,
                                   status=None if status == "全部" else status)

    # 關鍵指標
    st.subheader("關鍵指標")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    total = len(df)
    closed = len(df[df["status"] == "已解決"])
    avg_close = svc.get_avg_close_time(df).total_seconds() / 3600 if closed else 0
    unassigned = len(df[df["assignee_id"].isna()])

    kpi_col1.metric("總案件", total)
    kpi_col2.metric("已結案", closed)
    kpi_col3.metric("平均結案時數", f"{avg_close:.1f}")
    kpi_col4.metric("未指派", unassigned, delta="待指派" if unassigned else "OK", delta_color="inverse")

    # 趨勢圖
    st.subheader("案件趨勢")
    trend = svc.get_daily_trend(df)
    st.line_chart(trend.set_index("date"))

    # 負載圖
    st.subheader("個人負載")
    load = svc.get_assignee_load(df)
    st.bar_chart(load.set_index("assignee"))

    # 詳細表
    st.subheader("明細")
    st.dataframe(df)

    # 匯出
    csv = df.to_csv(index=False)
    st.download_button("下載 CSV", data=csv, file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                       mime="text/csv")
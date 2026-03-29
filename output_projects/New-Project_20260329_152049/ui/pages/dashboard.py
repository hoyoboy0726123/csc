import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.analytics_service import AnalyticsService


def render():
    st.set_page_config(page_title="儀表板 - AI-CSM", layout="wide")
    st.title("AI 客服案件管理系統 - 儀表板")

    # 初始化服務
    analytics = AnalyticsService()

    # 基本統計卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total = analytics.total_tickets()
        st.metric("總案件數", total)
    with col2:
        opened = analytics.opened_today()
        st.metric("今日新增", opened)
    with col3:
        pending = analytics.pending_count()
        st.metric("待處理", pending)
    with col4:
        avg_close = analytics.avg_close_days()
        st.metric("平均結案天數", f"{avg_close:.1f}")

    # 趨勢圖
    st.subheader("每日新增趨勢（近 30 天）")
    trend_df = analytics.daily_trend(days=30)
    if not trend_df.empty:
        st.line_chart(trend_df.set_index("date")["count"])
    else:
        st.info("暫無資料")

    # 個人負載
    st.subheader("個人負載（前 10 名）")
    load_df = analytics.assignee_load(limit=10)
    if not load_df.empty:
        st.bar_chart(load_df.set_index("assignee")["count"])
    else:
        st.info("暫無資料")

    # 狀態分布圓餅圖
    st.subheader("案件狀態分布")
    status_df = analytics.status_distribution()
    if not status_df.empty:
        st.write(status_df)
    else:
        st.info("暫無資料")

    # 最近更新
    st.subheader("最近更新（近 5 筆）")
    recent_df = analytics.recent_updates(limit=5)
    if not recent_df.empty:
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("暫無資料")

    # 手動刷新
    if st.button("刷新資料"):
        st.rerun()
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta


def plot_trend(df: pd.DataFrame) -> go.Figure:
    """
    繪製案件趨勢線圖：每日新增量與累計量
    df 需含欄位：created_at（datetime）
    """
    df["date"] = pd.to_datetime(df["created_at"]).dt.date
    daily = (
        df.groupby("date")
        .size()
        .reset_index(name="count")
        .sort_values("date")
    )
    daily["cumsum"] = daily["count"].cumsum()

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=["每日新增案件", "累計案件"],
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["count"],
            mode="lines+markers",
            name="每日新增",
            line=dict(color="#007acc"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["cumsum"],
            mode="lines+markers",
            name="累計",
            line=dict(color="#ff7f0e"),
        ),
        row=2,
        col=1,
    )
    fig.update_layout(height=500, title_text="案件趨勢")
    fig.update_xaxes(title_text="日期", row=2, col=1)
    fig.update_yaxes(title_text="數量", row=1, col=1)
    fig.update_yaxes(title_text="累計", row=2, col=1)
    return fig


def plot_load(df: pd.DataFrame) -> go.Figure:
    """
    繪製個人負載長條圖：每人待處理＋處理中案件數
    df 需含欄位：assignee_id、status
    """
    load = (
        df[df["status"].isin(["待處理", "處理中"])]
        .groupby(["assignee_id", "status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "待處理" not in load.columns:
        load["待處理"] = 0
    if "處理中" not in load.columns:
        load["處理中"] = 0

    fig = px.bar(
        load,
        x="assignee_id",
        y=["待處理", "處理中"],
        title="個人負載",
        labels={"value": "案件數", "assignee_id": "負責人"},
        height=400,
    )
    fig.update_layout(barmode="stack")
    return fig
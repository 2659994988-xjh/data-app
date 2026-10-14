"""Delivery Lens — historical Olist delivery performance dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from delivery_metrics import (
    ANALYSIS_END,
    ANALYSIS_START,
    analysis_orders,
    load_orders,
    state_rates,
    summary,
    weekly_rates,
)


DATA_PATH = Path(__file__).parent / "data" / "olist_delivery_orders.csv"
INK = "#11233f"
TEAL = "#087f79"
CORAL = "#ed6a5a"
GRID = "#e6edf1"

st.set_page_config(
    page_title="XuJinghan · Delivery Lens | Olist 订单延迟监控",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family: 'DM Sans','Noto Sans SC',sans-serif;}
[data-testid="stApp"] {background: #f5f8fa; color: #11233f;}
.block-container {max-width: 1240px; padding-top: 2.2rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {background: #11233f;}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color: #edf7f7 !important;}
[data-testid="stSidebar"] [role="spinbutton"], [data-testid="stSidebar"] input {color: #11233f !important;}
.eyebrow {font-size: .74rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: #087f79;}
.hero {background: linear-gradient(120deg,#11233f 0%,#174c60 72%,#087f79 100%); border-radius: 22px; padding: 28px 34px 30px; color: #fff; margin-bottom: 22px; box-shadow: 0 16px 40px rgba(17,35,63,.10);}
.hero h1 {font-size: clamp(1.65rem,3vw,2.65rem); letter-spacing: -.035em; margin: .3rem 0 .45rem; color: #fff;}
.hero p {margin: 0; max-width: 780px; color: #d9e9ec; font-size: .98rem;}
.hero .eyebrow {color: #9ee4da;}
.source-line {font-size: .82rem; color: #66758b; margin: -3px 0 22px;}
.section-kicker {color: #087f79; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; margin-top: 16px;}
.section-title {font-size: 1.33rem; font-weight: 700; color: #11233f; margin: 2px 0 6px;}
.section-subtitle {font-size: .88rem; color: #66758b; margin-bottom: 12px;}
[data-testid="stMetric"] {background: #fff; border: 1px solid #e5edf0; border-radius: 18px; padding: 19px 20px; box-shadow: 0 5px 20px rgba(22,48,67,.045);}
[data-testid="stMetricLabel"] {color: #66758b; font-size: .91rem;}
[data-testid="stMetricValue"] {color: #11233f; font-size: 2rem; font-weight: 700;}
.insight {background: #e9f5f2; border-left: 4px solid #087f79; border-radius: 0 12px 12px 0; padding: 12px 16px; color: #193d48; font-size: .91rem; margin: 11px 0 16px;}
.footnote {font-size: .79rem; color: #66758b; line-height: 1.5;}
</style>
""",
)


@st.cache_data(show_spinner=False)
def get_data() -> pd.DataFrame:
    return analysis_orders(load_orders(DATA_PATH))


try:
    all_orders = get_data()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"无法载入订单数据：{exc}")
    st.stop()

with st.sidebar:
    st.markdown("### DELIVERY LENS")
    st.caption("运营复盘 / Historical operations")
    st.divider()
    st.markdown("#### 查看范围")
    selected_dates = st.date_input(
        "承诺送达日期",
        value=(ANALYSIS_START.date(), ANALYSIS_END.date()),
        min_value=ANALYSIS_START.date(),
        max_value=ANALYSIS_END.date(),
        help="按订单承诺送达日期分组，而不是实际送达日期。",
    )
    states = sorted(all_orders["customer_state"].dropna().unique().tolist())
    selected_state = st.selectbox(
        "收货目的地州",
        options=["全部州", *states],
        help="目的地用于定位需要调查的区域，不代表延误原因。",
    )
    st.divider()
    st.caption("数据为 Olist 公开历史快照，不显示当前在途订单。")

if not isinstance(selected_dates, tuple) or len(selected_dates) != 2:
    st.info("请选择开始和结束日期。")
    st.stop()

start_date, end_date = selected_dates
if start_date > end_date:
    st.warning("开始日期不能晚于结束日期。")
    st.stop()

filtered = all_orders.loc[
    all_orders["promise_date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
    & (all_orders["customer_state"].eq(selected_state) if selected_state != "全部州" else True)
].copy()

st.html(
    """
<div class="hero">
  <div class="eyebrow">XUJINGHAN · DELIVERY LENS</div>
  <h1>订单延迟交付监控</h1>
  <p>面向 Olist 物流运营经理：每周判断承诺送达是否变差，并确定优先调查的目的地州。</p>
</div>
""",
)
st.html(
    "<div class='source-line'>数据：Olist / Kaggle 历史快照 · 分析区间：2017-03—2018-08 · "
    "实际生产建议每晚刷新、每周一复盘；此演示不自动更新。</div>",
)

if filtered.empty:
    st.warning("当前筛选条件下没有符合口径的已送达订单。请扩大日期范围或增加州。")
    st.stop()

metrics = summary(filtered)
st.html('<div class="section-kicker">01 / 核心指标</div>')
columns = st.columns(3, gap="medium")
with columns[0]:
    st.metric("延迟交付率", f"{metrics['late_rate']:.1%}", help="延迟订单数 ÷ 有有效日期的已送达订单数", border=True)
with columns[1]:
    st.metric("延迟订单", f"{metrics['late_orders']:,}", help="实际送达日期晚于承诺送达日期", border=True)
with columns[2]:
    st.metric("延迟天数中位数", f"{metrics['median_late_days']:.0f} 天", help="只在延迟订单中计算；比平均值更不受极端订单影响", border=True)

weekly = weekly_rates(filtered)
regions = state_rates(filtered, minimum_orders=200).head(8)
if not regions.empty:
    leading = regions.iloc[0]
    st.html(
        f"<div class='insight'><b>排查线索：</b>{leading['customer_state']} 州在所选范围有 "
        f"<b>{int(leading['late_orders']):,}</b> 笔延迟（{leading['late_rate']:.1%}）。"
        "先核对该地区订单履约及承运商记录；地区差异本身不能证明根因。</div>",
    )

st.html('<div class="section-kicker">02 / 定位变化</div>')
st.html('<div class="section-title">何时变差，影响集中在哪里？</div>')
st.html('<div class="section-subtitle">趋势图每个点代表一个承诺送达周，横轴只按月标日期以免拥挤；地区图按延迟订单数排序。</div>')

left, right = st.columns([1.35, 1], gap="large")
with left:
    st.markdown("**每周延迟交付率 · 每点一周**")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["late_rate"] * 100,
            mode="lines+markers",
            line=dict(color=TEAL, width=3),
            marker=dict(size=5, color=TEAL),
            customdata=weekly[["late_orders", "orders"]].to_numpy(),
            hovertemplate="承诺周起始：%{x|%Y-%m-%d}<br>延迟率 %{y:.1f}%<br>延迟 %{customdata[0]:,} / %{customdata[1]:,} 笔<extra></extra>",
        )
    )
    fig.update_layout(
        height=345,
        margin=dict(l=8, r=12, t=14, b=6),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        showlegend=False,
        font=dict(family="DM Sans, Noto Sans SC", color=INK, size=12),
        xaxis=dict(title="承诺送达周（日期刻度按月）", showgrid=False, tickformat="%Y-%m", tickangle=-35),
        yaxis=dict(title="延迟率 (%)", ticksuffix="%", gridcolor=GRID, zeroline=False, rangemode="tozero"),
        hoverlabel=dict(bgcolor=INK, font_color="#fff"),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, alt="每周延迟交付率趋势")

with right:
    st.markdown("**延迟订单最多的目的地州**")
    if regions.empty:
        st.info("所选范围内各州订单数均少于 200，暂不比较地区。")
    else:
        plot_regions = regions.iloc[::-1]
        fig = go.Figure(
            go.Bar(
                x=plot_regions["late_orders"],
                y=plot_regions["customer_state"],
                orientation="h",
                marker=dict(color=CORAL, line=dict(width=0)),
                customdata=plot_regions[["late_rate", "orders"]].to_numpy(),
                hovertemplate="%{y}<br>延迟 %{x:,} 笔<br>延迟率 %{customdata[0]:.1%}<br>样本 %{customdata[1]:,} 笔<extra></extra>",
            )
        )
        fig.update_layout(
            height=345,
            margin=dict(l=8, r=12, t=14, b=6),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            showlegend=False,
            font=dict(family="DM Sans, Noto Sans SC", color=INK, size=12),
            xaxis=dict(title="延迟订单数", gridcolor=GRID, zeroline=False),
            yaxis=dict(showgrid=False),
            hoverlabel=dict(bgcolor=INK, font_color="#fff"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, alt="延迟订单数最多的目的地州")

st.html('<div class="section-kicker">03 / 订单明细</div>')
st.html('<div class="section-title">供复盘的延迟订单</div>')
st.html('<div class="section-subtitle">优先查看延迟天数较长的历史订单；这不是当前待处理工单队列。</div>')
late_detail = (
    filtered.loc[filtered["is_late"], [
        "order_id",
        "customer_state",
        "promise_date",
        "delivered_date",
        "late_days",
    ]]
    .sort_values("late_days", ascending=False)
    .head(20)
    .rename(columns={
        "order_id": "订单 ID",
        "customer_state": "目的地州",
        "promise_date": "承诺送达",
        "delivered_date": "实际送达",
        "late_days": "延迟天数",
    })
)
st.dataframe(
    late_detail,
    hide_index=True,
    width="stretch",
    alt="延迟天数最长的二十笔历史订单",
    column_config={
        "承诺送达": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "实际送达": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "延迟天数": st.column_config.NumberColumn(format="%d 天"),
    },
)
st.html(
    "<div class='footnote'>口径：只包括状态为 delivered、承诺与实际送达日期都有效的订单；"
    "按日历日期比较，同一天送达算准时。目的地州仅用于确定排查顺序。"
    "2016 年初期和 2018 年末期月份样本不完整，已从默认分析区间排除。</div>",
)

"""
In an environment with streamlit, plotly and duckdb installed,
Run with `streamlit run streamlit_app.py`
"""
# 把dataframe用sql来查询
import duckdb 
import pandas as pd
# 更可定制化的plotly图形
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
# 自定义的侧边栏多页面
# from st_pages import Page,  Section, show_pages

#######################################
# PAGE SETUP
#######################################

st.set_page_config(page_title="代发数据仪表盘", page_icon=":bar_chart:", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={})

# Specify what pages should be shown in the sidebar, and what their titles 
# and icons should be
# show_pages(
#     [
#         Section(name="数据维度",icon=":star:"),
#         Page("streamlit_app.py", "支行概览", ""),
#         Page("pages/数据维度/团队.py", "团队维度", ""),
#         Page("pages/数据维度/客户经理.py", "客户经理维度", ""),
#         Page("pages/数据维度/客户.py", "客户维度", ""),
#         Section(name="参数设置",icon=":star:"),
#         Page("pages/参数设置/KPI参数.py", "KPI参数", "")
#     ]
# )

st.title("代发数据仪表盘")
st.markdown("浦发银行 2023")

def initialize_kpi():
    if 'kpi_money' not in st.session_state:
        st.session_state['kpi_money'] = 300.0
    if 'kpi_customers' not in st.session_state:
        st.session_state['kpi_customers'] = 400.0
    if 'kpi_aum' not in st.session_state:
        st.session_state['kpi_aum'] = 500.0 

initialize_kpi()

with st.sidebar:
    st.header("功能")
    uploaded_files = st.file_uploader("上传代发最新数据",accept_multiple_files=True)

if uploaded_files is None:
    # st.info(" Upload a file through config", icon="ℹ️")
    st.stop() #NOTE:?      

#######################################
# DATA LOADING
#######################################

# 缓存结果，只要输入一样，结果就不变
@st.cache_data
def load_data(paths: list):
    for path in paths:
        df = pd.read_excel(path)
    return df

df = load_data(uploaded_files)
all_months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

with st.expander("Data Preview"):
    st.dataframe(
        df,
        column_config={"Year": st.column_config.NumberColumn(format="%d")},
    )

#######################################
# VISUALIZATION METHODS
#######################################


def plot_metric(label, value, prefix="", suffix="", show_graph=False, color_graph=""):
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            value=value,
            gauge={"axis": {"visible": False}},
            number={
                "prefix": prefix,
                "suffix": suffix,
                "font.size": 28,
            },
            title={
                "text": label,
                "font": {"size": 24},
            },
        )
    )

    if show_graph:
        fig.add_trace(
            go.Scatter(
                y=random.sample(range(0, 101), 30),
                hoverinfo="skip",
                fill="tozeroy",
                fillcolor=color_graph,
                line={
                    "color": color_graph,
                },
            )
        )

    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)
    fig.update_layout(
        # paper_bgcolor="lightgrey",
        margin=dict(t=30, b=0),
        showlegend=False,
        plot_bgcolor="white",
        height=100,
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_gauge(
    indicator_number, indicator_color, indicator_suffix, indicator_title, max_bound
):
    fig = go.Figure(
        go.Indicator(
            value=indicator_number,
            mode="gauge+number",
            domain={"x": [0, 1], "y": [0, 1]},
            number={
                "suffix": indicator_suffix,
                "font.size": 26,
            },
            gauge={
                "axis": {"range": [0, max_bound], "tickwidth": 1},
                "bar": {"color": indicator_color},
            },
            title={
                "text": indicator_title,
                "font": {"size": 28},
            },
        )
    )
    fig.update_layout(
        # paper_bgcolor="lightgrey",
        height=200,
        margin=dict(l=10, r=10, t=50, b=10, pad=8),
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_top_right():
    sales_data = duckdb.sql(
        f"""
        WITH sales_data AS (
            UNPIVOT ( 
                SELECT 
                    Scenario,
                    business_unit,
                    {','.join(all_months)} 
                    FROM df 
                    WHERE Year='2023' 
                    AND Account='Sales' 
                ) 
            ON {','.join(all_months)}
            INTO
                NAME month
                VALUE sales
        ),

        aggregated_sales AS (
            SELECT
                Scenario,
                business_unit,
                SUM(sales) AS sales
            FROM sales_data
            GROUP BY Scenario, business_unit
        )
        
        SELECT * FROM aggregated_sales
        """
    ).df()

    fig = px.bar(
        sales_data,
        x="business_unit",
        y="sales",
        color="Scenario",
        barmode="group",
        text_auto=".2s",
        title="Sales for Year 2023",
        height=400,
    )
    fig.update_traces(
        textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_bottom_left():
    sales_data = duckdb.sql(
        f"""
        WITH sales_data AS (
            SELECT 
            Scenario,{','.join(all_months)} 
            FROM df 
            WHERE Year='2023' 
            AND Account='Sales'
            AND business_unit='Software'
        )

        UNPIVOT sales_data 
        ON {','.join(all_months)}
        INTO
            NAME month
            VALUE sales
    """
    ).df()

    fig = px.line(
        sales_data,
        x="month",
        y="sales",
        color="Scenario",
        markers=True,
        text="sales",
        title="Monthly Budget vs Forecast 2023",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)


def plot_bottom_right():
    sales_data = duckdb.sql(
        f"""
        WITH sales_data AS (
            UNPIVOT ( 
                SELECT 
                    Account,Year,{','.join([f'ABS({month}) AS {month}' for month in all_months])}
                    FROM df 
                    WHERE Scenario='Actuals'
                    AND Account!='Sales'
                ) 
            ON {','.join(all_months)}
            INTO
                NAME year
                VALUE sales
        ),

        aggregated_sales AS (
            SELECT
                Account,
                Year,
                SUM(sales) AS sales
            FROM sales_data
            GROUP BY Account, Year
        )
        
        SELECT * FROM aggregated_sales
    """
    ).df()

    fig = px.bar(
        sales_data,
        x="Year",
        y="sales",
        color="Account",
        title="Actual Yearly Sales Per Account",
    )
    st.plotly_chart(fig, use_container_width=True)


#######################################
# STREAMLIT LAYOUT
#######################################

top_left_column, top_right_column = st.columns((2, 1))
bottom_left_column, bottom_right_column = st.columns(2)

with top_left_column:
    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        plot_metric(
            "Total Accounts Receivable",
            6621280,
            prefix="$",
            suffix="",
            show_graph=True,
            color_graph="rgba(0, 104, 201, 0.2)",
        )
        plot_gauge(1.86, "#0068C9", "%", "Current Ratio", 3)

    with column_2:
        plot_metric(
            "Total Accounts Payable",
            1630270,
            prefix="$",
            suffix="",
            show_graph=True,
            color_graph="rgba(255, 43, 43, 0.2)",
        )
        plot_gauge(10, "#FF8700", " days", "In Stock", 31)

    with column_3:
        plot_metric("Equity Ratio", 75.38, prefix="", suffix=" %", show_graph=False)
        plot_gauge(7, "#FF2B2B", " days", "Out Stock", 31)
        
    with column_4:
        plot_metric("Debt Equity", 1.10, prefix="", suffix=" %", show_graph=False)
        plot_gauge(28, "#29B09D", " days", "Delay", 31)

with top_right_column:
    plot_top_right()

with bottom_left_column:
    plot_bottom_left()

with bottom_right_column:
    plot_bottom_right()

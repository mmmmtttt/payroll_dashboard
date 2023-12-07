import streamlit as st

st.write("# KPI参数设置")

money_amount_kpi = st.number_input("代发金额指标数", value=None, placeholder=st.session_state['kpi_money'])

customer_num_kpi = st.number_input("代发客户数指标", value=None, placeholder=st.session_state['kpi_customers'])

customer_aum_kpi = st.number_input("代发客户AUM指标", value=None, placeholder=st.session_state['kpi_aum'])

def save_kpi():
    if money_amount_kpi is not None:
        st.session_state['kpi_money']=money_amount_kpi
    if customer_num_kpi is not None:
        st.session_state['kpi_customers']=customer_num_kpi
    if customer_aum_kpi is not None:
        st.session_state['kpi_aum']=customer_aum_kpi


st.button("保存", type="primary",on_click=save_kpi)


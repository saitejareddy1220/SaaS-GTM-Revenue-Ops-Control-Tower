import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).parent.parent / '.env')

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'saas_analytics')
DB_USER = os.getenv('POSTGRES_USER', 'analytics_user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'analytics_pass')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


@st.cache_resource
def get_db_engine():
    """Create cached database connection."""
    return create_engine(DATABASE_URL)


@st.cache_data(ttl=300)
def run_query(query):
    """Execute SQL query with caching."""
    engine = get_db_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


st.set_page_config(
    page_title="SaaS GTM Control Tower",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sky blue background
st.markdown("""
    <style>
    .stApp {
        background-color: #87CEEB;
    }
    .main .block-container {
        background-color: #E6F3FF;
        padding: 2rem;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("SaaS GTM Revenue & Ops Control Tower")
st.markdown("*Unified view of pipeline, revenue, retention, and operational health*")

# Global filters in sidebar
st.sidebar.header("Filters")

# Get filter options
accounts = run_query("SELECT DISTINCT segment, region, acquisition_channel FROM public_marts.dim_account ORDER BY 1, 2, 3")

segment_options = ['All'] + sorted(accounts['segment'].dropna().unique().tolist())
region_options = ['All'] + sorted(accounts['region'].dropna().unique().tolist())
channel_options = ['All'] + sorted(accounts['acquisition_channel'].dropna().unique().tolist())

selected_segment = st.sidebar.selectbox("Segment", segment_options)
selected_region = st.sidebar.selectbox("Region", region_options)
selected_channel = st.sidebar.selectbox("Acquisition Channel", channel_options)

# Build WHERE clause for filters
filter_conditions = []
if selected_segment != 'All':
    filter_conditions.append(f"da.segment = '{selected_segment}'")
if selected_region != 'All':
    filter_conditions.append(f"da.region = '{selected_region}'")
if selected_channel != 'All':
    filter_conditions.append(f"da.acquisition_channel = '{selected_channel}'")

where_clause = " AND " + " AND ".join(filter_conditions) if filter_conditions else ""

# Navigation
page = st.sidebar.radio(
    "Navigate",
    ["Executive Overview", "Funnel & Pipeline", "Retention & Cohorts", "Support & Quality", "Anomalies"]
)




# PAGE 1: EXECUTIVE OVERVIEW
if page == "Executive Overview":
    st.header("Executive Overview")
    
    # KPI Cards
    kpi_query = f"""
    WITH latest_month AS (
        SELECT MAX(revenue_month) as max_month
        FROM public_marts.fct_revenue_monthly
    ),
    current_metrics AS (
        SELECT
            SUM(r.mrr) as current_mrr,
            SUM(r.arr) as current_arr,
            AVG(CASE WHEN r.nrr IS NOT NULL THEN r.nrr ELSE 0 END) as avg_nrr,
            SUM(r.churned_mrr) as churned_mrr,
            COUNT(DISTINCT r.account_id) as active_accounts
        FROM public_marts.fct_revenue_monthly r
        JOIN public_marts.dim_account da ON r.account_id = da.account_id
        WHERE r.revenue_month = (SELECT max_month FROM latest_month)
        {where_clause}
    ),
    activation_metrics AS (
        SELECT AVG(activation_rate) as avg_activation_rate
        FROM public_marts.fct_activation a
        JOIN public_marts.dim_account da ON a.account_id = da.account_id
        WHERE 1=1 {where_clause}
    ),
    cac_metrics AS (
        SELECT AVG(cac) as avg_cac
        FROM public_marts.fct_cac_ltv
    )
    SELECT
        cm.current_mrr,
        cm.current_arr,
        cm.avg_nrr,
        cm.churned_mrr,
        cm.active_accounts,
        am.avg_activation_rate,
        cm2.avg_cac
    FROM current_metrics cm
    CROSS JOIN activation_metrics am
    CROSS JOIN cac_metrics cm2
    """
    
    kpis = run_query(kpi_query)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("MRR", f"${kpis['current_mrr'].iloc[0]:,.0f}")
        st.metric("ARR", f"${kpis['current_arr'].iloc[0]:,.0f}")
    
    with col2:
        nrr_pct = kpis['avg_nrr'].iloc[0] * 100 if pd.notna(kpis['avg_nrr'].iloc[0]) else 0
        st.metric("NRR", f"{nrr_pct:.1f}%")
        st.metric("Active Accounts", f"{kpis['active_accounts'].iloc[0]:,.0f}")
    
    with col3:
        activation_pct = kpis['avg_activation_rate'].iloc[0] * 100 if pd.notna(kpis['avg_activation_rate'].iloc[0]) else 0
        st.metric("Activation Rate", f"{activation_pct:.1f}%")
        st.metric("Churned MRR (Latest)", f"${kpis['churned_mrr'].iloc[0]:,.0f}")
    
    with col4:
        avg_cac = kpis['avg_cac'].iloc[0] if pd.notna(kpis['avg_cac'].iloc[0]) else 0
        st.metric("Avg CAC", f"${avg_cac:,.0f}")
    
    st.markdown("---")
    
    # Trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("MRR Trend")
        mrr_trend = run_query(f"""
            SELECT
                r.revenue_month,
                SUM(r.mrr) as total_mrr,
                SUM(r.new_mrr) as new_mrr,
                SUM(r.expansion_mrr) as expansion_mrr,
                SUM(r.churned_mrr) as churned_mrr
            FROM public_marts.fct_revenue_monthly r
            JOIN public_marts.dim_account da ON r.account_id = da.account_id
            WHERE 1=1 {where_clause}
            GROUP BY 1
            ORDER BY 1
        """)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=mrr_trend['revenue_month'], y=mrr_trend['total_mrr'],
                                mode='lines+markers', name='Total MRR', line=dict(width=3)))
        fig.add_trace(go.Scatter(x=mrr_trend['revenue_month'], y=mrr_trend['new_mrr'],
                                mode='lines', name='New MRR', line=dict(dash='dot')))
        fig.add_trace(go.Scatter(x=mrr_trend['revenue_month'], y=mrr_trend['expansion_mrr'],
                                mode='lines', name='Expansion', line=dict(dash='dot')))
        fig.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Revenue by Segment")
        segment_rev = run_query(f"""
            SELECT
                da.segment,
                SUM(r.mrr) as total_mrr
            FROM public_marts.fct_revenue_monthly r
            JOIN public_marts.dim_account da ON r.account_id = da.account_id
            WHERE r.revenue_month = (SELECT MAX(revenue_month) FROM public_marts.fct_revenue_monthly)
            {where_clause}
            GROUP BY 1
            ORDER BY 2 DESC
        """)
        
        fig = px.pie(segment_rev, values='total_mrr', names='segment', hole=0.4)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


# PAGE 2: FUNNEL & PIPELINE
elif page == "Funnel & Pipeline":
    st.header("Funnel & Pipeline Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Win Rate by Segment")
        pipeline = run_query("""
            SELECT segment, win_rate, won_deals, lost_deals
            FROM public_marts.fct_pipeline
            WHERE win_rate IS NOT NULL
            ORDER BY segment
        """)
        
        fig = px.bar(pipeline, x='segment', y='win_rate', text='win_rate',
                    labels={'win_rate': 'Win Rate', 'segment': 'Segment'})
        fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(pipeline, use_container_width=True)
    
    with col2:
        st.subheader("Sales Cycle Length")
        sales_cycle = run_query("""
            SELECT segment, avg_sales_cycle_days
            FROM public_marts.fct_pipeline
            WHERE stage = 'Closed Won'
            ORDER BY segment
        """)
        
        fig = px.bar(sales_cycle, x='segment', y='avg_sales_cycle_days',
                    labels={'avg_sales_cycle_days': 'Avg Days', 'segment': 'Segment'},
                    color='avg_sales_cycle_days', color_continuous_scale='Blues')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Deal Value Distribution")
    deal_value = run_query("""
        SELECT
            segment,
            stage,
            avg_deal_value,
            deal_count
        FROM public_marts.fct_pipeline
        WHERE stage IN ('Closed Won', 'Closed Lost')
        ORDER BY segment, stage
    """)
    
    fig = px.bar(deal_value, x='segment', y='avg_deal_value', color='stage',
                barmode='group', text='deal_count',
                labels={'avg_deal_value': 'Avg Deal Value', 'deal_count': 'Count'})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


# PAGE 3: RETENTION & COHORTS
elif page == "Retention & Cohorts":
    st.header("Retention & Cohort Analysis")
    
    st.subheader("Cohort Retention Heatmap")
    
    cohort_data = run_query("""
        SELECT
            cohort_month,
            months_since_cohort,
            retention_rate
        FROM public_marts.fct_retention
        WHERE months_since_cohort <= 12
        ORDER BY cohort_month, months_since_cohort
    """)
    
    # Pivot for heatmap
    cohort_pivot = cohort_data.pivot(index='cohort_month', columns='months_since_cohort', values='retention_rate')
    
    fig = go.Figure(data=go.Heatmap(
        z=cohort_pivot.values * 100,
        x=cohort_pivot.columns,
        y=cohort_pivot.index,
        colorscale='RdYlGn',
        text=cohort_pivot.values * 100,
        texttemplate='%{text:.0f}%',
        textfont={"size": 10},
        colorbar=dict(title="Retention %")
    ))
    
    fig.update_layout(
        xaxis_title="Months Since Cohort",
        yaxis_title="Cohort Month",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Activation vs Retention")
        activation_retention = run_query(f"""
            SELECT
                a.segment,
                AVG(a.activation_rate) as avg_activation,
                AVG(r.retention_rate) as avg_retention
            FROM public_marts.fct_activation a
            JOIN public_marts.dim_account da ON a.account_id = da.account_id
            JOIN public_marts.fct_retention r ON date_trunc('month', da.created_at) = r.cohort_month
            WHERE r.months_since_cohort = 6
            {where_clause}
            GROUP BY 1
        """)
        
        fig = px.scatter(activation_retention, x='avg_activation', y='avg_retention',
                        size=[100]*len(activation_retention), text='segment',
                        labels={'avg_activation': 'Activation Rate', 'avg_retention': '6-Month Retention'})
        fig.update_traces(textposition='top center')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Churn by Cohort")
        churn_trend = run_query("""
            SELECT
                cohort_month,
                AVG(churn_rate) as avg_churn_rate
            FROM public_marts.fct_retention
            WHERE months_since_cohort BETWEEN 3 AND 6
            GROUP BY 1
            ORDER BY 1
        """)
        
        fig = px.line(churn_trend, x='cohort_month', y='avg_churn_rate',
                     markers=True, labels={'avg_churn_rate': 'Avg Churn Rate (3-6mo)'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


# PAGE 4: SUPPORT & QUALITY
elif page == "Support & Quality":
    st.header("Support & Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    support_summary = run_query(f"""
        SELECT
            SUM(total_tickets) as total_tickets,
            AVG(sla_breach_rate) as avg_sla_breach_rate,
            AVG(avg_resolution_hours) as avg_resolution_hours
        FROM public_marts.fct_support s
        JOIN public_marts.dim_account da ON s.account_id = da.account_id
        WHERE 1=1 {where_clause}
    """)
    
    with col1:
        st.metric("Total Tickets", f"{support_summary['total_tickets'].iloc[0]:,.0f}")
    
    with col2:
        breach_rate = support_summary['avg_sla_breach_rate'].iloc[0] * 100
        st.metric("Avg SLA Breach Rate", f"{breach_rate:.1f}%")
    
    with col3:
        avg_res = support_summary['avg_resolution_hours'].iloc[0]
        st.metric("Avg Resolution Time", f"{avg_res:.1f} hrs")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ticket Volume by Segment")
        tickets_by_segment = run_query(f"""
            SELECT
                da.segment,
                SUM(s.total_tickets) as tickets,
                SUM(s.critical_tickets) as critical,
                SUM(s.high_tickets) as high
            FROM public_marts.fct_support s
            JOIN public_marts.dim_account da ON s.account_id = da.account_id
            WHERE 1=1 {where_clause}
            GROUP BY 1
            ORDER BY 2 DESC
        """)
        
        fig = px.bar(tickets_by_segment, x='segment', y=['critical', 'high', 'tickets'],
                    barmode='group', labels={'value': 'Ticket Count', 'variable': 'Severity'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("SLA Performance by Region")
        sla_by_region = run_query(f"""
            SELECT
                da.region,
                AVG(s.sla_breach_rate) as breach_rate,
                AVG(s.median_resolution_hours) as median_res_hours
            FROM public_marts.fct_support s
            JOIN public_marts.dim_account da ON s.account_id = da.account_id
            WHERE 1=1 {where_clause}
            GROUP BY 1
            ORDER BY 2 DESC
        """)
        
        fig = px.bar(sla_by_region, x='region', y='breach_rate',
                    labels={'breach_rate': 'SLA Breach Rate', 'region': 'Region'},
                    color='breach_rate', color_continuous_scale='Reds')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


# PAGE 5: ANOMALIES
elif page == "Anomalies":
    st.header("Metric Anomaly Detection")
    
    st.markdown("Flagging month-over-month changes >10%")
    
    anomalies = run_query("""
        SELECT
            metric_month,
            metric_name,
            metric_value,
            prev_month_value,
            pct_change,
            anomaly_severity,
            anomaly_type
        FROM public_marts.fct_anomalies
        ORDER BY metric_month DESC, ABS(pct_change) DESC
        LIMIT 50
    """)
    
    if len(anomalies) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Recent Anomalies")
            
            # Color code by type
            def highlight_anomaly(row):
                if row['anomaly_type'] == 'Spike':
                    return ['background-color: #d4edda'] * len(row)
                elif row['anomaly_type'] == 'Drop':
                    return ['background-color: #f8d7da'] * len(row)
                return [''] * len(row)
            
            styled_df = anomalies.style.apply(highlight_anomaly, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        
        with col2:
            st.subheader("Anomaly Distribution")
            
            anomaly_counts = anomalies['anomaly_type'].value_counts()
            
            fig = px.pie(values=anomaly_counts.values, names=anomaly_counts.index,
                        color=anomaly_counts.index,
                        color_discrete_map={'Spike': '#28a745', 'Drop': '#dc3545'})
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Severity Breakdown")
            severity_counts = anomalies['anomaly_severity'].value_counts()
            st.write(severity_counts)
    else:
        st.info("No significant anomalies detected in the current dataset.")
    
    st.markdown("---")
    st.subheader("Metric Trend Visualization")
    
    selected_metric = st.selectbox("Select Metric", anomalies['metric_name'].unique())
    
    metric_trend = run_query(f"""
        SELECT
            metric_month,
            metric_value,
            pct_change
        FROM public_marts.fct_anomalies
        WHERE metric_name = '{selected_metric}'
        ORDER BY metric_month
    """)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=metric_trend['metric_month'], y=metric_trend['metric_value'],
                            mode='lines+markers', name=selected_metric, line=dict(width=2)))
    fig.update_layout(height=400, hovermode='x unified',
                     yaxis_title=selected_metric, xaxis_title='Month')
    st.plotly_chart(fig, use_container_width=True)


st.sidebar.markdown("---")
st.sidebar.caption("Built with dbt + Streamlit")

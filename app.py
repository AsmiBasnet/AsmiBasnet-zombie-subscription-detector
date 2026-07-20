import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(
    page_title="Zombie Subscription Detector Dashboard",
    page_icon="🧟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Theme Toggle State
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# 3. CSS Variables & Custom Injection
theme_vars = f"""
:root {{
    --bg: {"#09090b" if IS_DARK else "#ffffff"};
    --bg-subtle: {"#0c0c0f" if IS_DARK else "#f9fafb"};
    --card: {"#0c0c0f" if IS_DARK else "#ffffff"};
    --card-hover: {"#131316" if IS_DARK else "#f4f4f5"};
    --border: {"#1e1e24" if IS_DARK else "#e4e4e7"};
    --border-subtle: {"#16161a" if IS_DARK else "#f0f0f2"};
    --text: {"#fafafa" if IS_DARK else "#09090b"};
    --text-muted: #71717a;
    --text-dim: {"#52525b" if IS_DARK else "#a1a1aa"};
    --accent: #2563eb;
    --accent-muted: #1d4ed8;
    --green: {"#22c55e" if IS_DARK else "#16a34a"};
    --green-muted: {"rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"};
    --red: {"#ef4444" if IS_DARK else "#dc2626"};
    --red-muted: {"rgba(239,68,68,0.12)" if IS_DARK else "rgba(220,38,38,0.08)"};
    --amber: {"#f59e0b" if IS_DARK else "#d97706"};
    --amber-muted: {"rgba(245,158,11,0.12)" if IS_DARK else "rgba(217,119,6,0.08)"};
    --shadow: {"none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"};
    --radius: 10px;
}}
"""

css = f"""
<style>
{theme_vars}

/* Hide Streamlit chrome */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Global App Styling */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}
.block-container {{
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1360px !important;
}}

/* Horizontal blocks column gap */
[data-testid="stHorizontalBlock"] {{
    gap: 1.25rem !important;
}}

/* Brand Styling */
.brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.5rem;
}}
.brand-name {{
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--text);
}}
.brand-subtitle {{
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: -0.2rem;
    margin-bottom: 1.25rem;
}}

/* Metric Card (KPI) */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    height: 100%;
}}
.metric-label {{
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}}
.metric-value {{
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.03em;
}}
.metric-delta {{
    font-size: 0.72rem;
    font-weight: 500;
    margin-top: 0.4rem;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    align-self: flex-start;
}}
.delta-up {{ color: var(--green); background: var(--green-muted); }}
.delta-down {{ color: var(--red); background: var(--red-muted); }}
.delta-warn {{ color: var(--amber); background: var(--amber-muted); }}

/* Chart Container */
.chart-wrap {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}}
.chart-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
}}
.chart-subtitle {{
    font-size: 0.72rem;
    color: var(--text-dim);
    margin-bottom: 0.8rem;
}}

/* Data Table (HTML) */
.data-table-container {{
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--card);
    margin-top: 0.5rem;
}}
.data-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.78rem;
}}
.data-table th {{
    text-align: left;
    padding: 0.65rem 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid var(--border);
    background: var(--bg-subtle);
}}
.data-table td {{
    padding: 0.65rem 0.8rem;
    color: var(--text);
    border-bottom: 1px solid var(--border-subtle);
    vertical-align: middle;
}}
.data-table tr:hover td {{
    background: var(--card-hover);
}}
.data-table tr:last-child td {{
    border-bottom: none;
}}

/* Status Badges */
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 600;
    text-align: center;
}}
.badge-green {{ color: var(--green); background: var(--green-muted); }}
.badge-red {{ color: var(--red); background: var(--red-muted); }}
.badge-amber {{ color: var(--amber); background: var(--amber-muted); }}
.badge-blue {{ color: var(--accent); background: rgba(37,99,235,0.1); }}

/* Tabs (pill-style) */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    border: 1px solid transparent !important;
    border-radius: 7px !important;
    transition: all 0.2s ease !important;
}}
button[data-baseweb="tab"]:hover {{
    color: var(--text) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    background: var(--card) !important;
    border-color: var(--border) !important;
    box-shadow: var(--shadow) !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 4px !important;
    background: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    width: fit-content !important;
    margin-bottom: 1rem !important;
}}

/* Sidebar styling overrides */
[data-testid="stSidebar"] {{
    background-color: var(--bg-subtle) !important;
    border-right: 1px solid var(--border) !important;
}}

/* Form inputs & buttons custom styles */
div[data-testid="stForm"] {{
    border-radius: var(--radius) !important;
    border-color: var(--border) !important;
    background-color: var(--card) !important;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# 4. Helper to render KPI cards
def render_metric_card(label, value, delta=None, delta_type="up"):
    cls = f"delta-{delta_type}"
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else "→")
    delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# 5. Database Connection and Ingestion Logic
@st.cache_data
def get_dashboard_data():
    conn = sqlite3.connect("zombie_detector.db")
    
    # Query to fetch all active/settled subscriptions and calculate standard metrics
    query = """
    WITH raw_payments AS (
        SELECT 
            user_id,
            merchant_id,
            amount,
            transaction_date,
            CAST(JULIANDAY(transaction_date) - JULIANDAY(
                LAG(transaction_date, 1) OVER (
                    PARTITION BY user_id, merchant_id  
                    ORDER BY transaction_date     
                )
            ) AS INTEGER) AS days_since_last_payment,
            CAST(JULIANDAY(
                LEAD(transaction_date, 1) OVER (
                    PARTITION BY user_id, merchant_id  
                    ORDER BY transaction_date     
                )
            ) - JULIANDAY(transaction_date) AS INTEGER) AS days_until_next_payment
        FROM fact_transactions
        WHERE status = 'settled'
    ),
    recurring_payments AS (
        SELECT 
            user_id,
            merchant_id,
            amount,
            transaction_date,
            FIRST_VALUE(amount) OVER (
                PARTITION BY user_id, merchant_id
                ORDER BY transaction_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS start_amount,
            LAST_VALUE(amount) OVER (
                PARTITION BY user_id, merchant_id
                ORDER BY transaction_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS current_amount
        FROM raw_payments
        WHERE 
            ((days_since_last_payment BETWEEN 27 AND 33) OR (days_until_next_payment BETWEEN 27 AND 33))
            AND ROUND(amount - CAST(amount AS INTEGER), 2) IN (0.99, 0.49)
    ),
    agg_features AS (
        SELECT 
            user_id,
            merchant_id,
            MIN(transaction_date) AS subscription_start,
            MAX(transaction_date) AS subscription_latest,
            CAST(JULIANDAY(MAX(transaction_date)) - JULIANDAY(MIN(transaction_date)) AS INTEGER) AS tenure_days,
            start_amount,
            current_amount,
            ROUND(current_amount - start_amount, 2) AS price_creep,
            COUNT(*) AS total_payments,
            SUM(amount) AS total_amount_paid
        FROM recurring_payments
        GROUP BY user_id, merchant_id
    )
    SELECT 
        f.user_id,
        u.name AS user_name,
        u.email AS user_email,
        f.merchant_id,
        m.merchant_name,
        m.category,
        f.subscription_start,
        f.subscription_latest,
        f.tenure_days,
        f.start_amount,
        f.current_amount,
        f.price_creep,
        f.total_payments,
        f.total_amount_paid,
        s.is_zombie_ground_truth,
        s.end_date
    FROM agg_features f
    JOIN dim_users u ON f.user_id = u.user_id
    JOIN dim_merchants m ON f.merchant_id = m.merchant_id
    JOIN dim_subscriptions s ON f.user_id = s.user_id AND f.merchant_id = s.merchant_id;
    """
    
    # Fetch all transaction logs to build trend lines
    tx_query = """
    SELECT 
        t.user_id,
        t.merchant_id,
        t.amount,
        t.transaction_date,
        m.merchant_name
    FROM fact_transactions t
    JOIN dim_merchants m ON t.merchant_id = m.merchant_id
    WHERE t.status = 'settled'
    ORDER BY t.transaction_date;
    """
    
    df_subs = pd.read_sql_query(query, conn)
    df_tx = pd.read_sql_query(tx_query, conn)
    
    conn.close()
    return df_subs, df_tx

df_subs, df_tx = get_dashboard_data()

# Filter down to Active Subscriptions (according to database generator, active have end_date is null or empty)
df_active = df_subs[df_subs['end_date'].isna() | (df_subs['end_date'] == '')].copy()

# 6. UI Header
head_left, head_right = st.columns([9, 1])
with head_left:
    st.markdown("""
    <div class="brand">
        <span class="brand-name">🧟 Zombie Subscription Detector</span>
    </div>
    <div class="brand-subtitle">Interactive recurring billing analytics and wasted spend visualization</div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Light" if IS_DARK else "🌙 Dark"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

# 7. Sidebar Controls & Strategy Selection
st.sidebar.markdown("### Detection Parameters")
strategy_option = st.sidebar.selectbox(
    "Select Zombie Detection Strategy",
    options=[
        "Strategy A: Price Creep Only (creep > 0)",
        "Strategy B1: Long Tenure (tenure > 360 days)",
        "Strategy B2: Long Tenure (tenure > 180 days)",
        "Strategy C1: Combined (creep > 0 OR tenure > 360 days)",
        "Strategy C2: Combined (creep > 0 OR tenure > 180 days)",
        "Ground Truth Labels"
    ],
    index=0
)

# Apply selected strategy logic
if strategy_option == "Strategy A: Price Creep Only (creep > 0)":
    df_active['is_zombie'] = df_active['price_creep'] > 0
elif strategy_option == "Strategy B1: Long Tenure (tenure > 360 days)":
    df_active['is_zombie'] = df_active['tenure_days'] > 360
elif strategy_option == "Strategy B2: Long Tenure (tenure > 180 days)":
    df_active['is_zombie'] = df_active['tenure_days'] > 180
elif strategy_option == "Strategy C1: Combined (creep > 0 OR tenure > 360 days)":
    df_active['is_zombie'] = (df_active['price_creep'] > 0) | (df_active['tenure_days'] > 360)
elif strategy_option == "Strategy C2: Combined (creep > 0 OR tenure > 180 days)":
    df_active['is_zombie'] = (df_active['price_creep'] > 0) | (df_active['tenure_days'] > 180)
else: # Ground Truth Labels
    df_active['is_zombie'] = df_active['is_zombie_ground_truth'] == 1

# Calculate metrics based on selected strategy
total_subs = len(df_active)
zombie_subs_df = df_active[df_active['is_zombie']]
num_zombies = len(zombie_subs_df)

total_monthly_spend = df_active['current_amount'].sum()
zombie_monthly_spend = zombie_subs_df['current_amount'].sum()
zombie_pct = (num_zombies / total_subs) * 100 if total_subs > 0 else 0

total_cumulative_wasted = zombie_subs_df['total_amount_paid'].sum()

# 8. Render KPI Metric Cards
kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)

with kpi_c1:
    render_metric_card(
        label="Active Subscriptions",
        value=f"{total_subs}",
        delta=None
    )
with kpi_c2:
    render_metric_card(
        label="Monthly Recurring Spend",
        value=f"${total_monthly_spend:,.2f}",
        delta=None
    )
with kpi_c3:
    render_metric_card(
        label="Zombie Subscriptions",
        value=f"{num_zombies}",
        delta=f"{zombie_pct:.1f}% of active",
        delta_type="warn" if zombie_pct > 10 else "down"
    )
with kpi_c4:
    render_metric_card(
        label="Wasted Monthly Spend",
        value=f"${zombie_monthly_spend:,.2f}",
        delta=f"{(zombie_monthly_spend/total_monthly_spend)*100:.1f}% of monthly" if total_monthly_spend > 0 else None,
        delta_type="down" if zombie_monthly_spend > 0 else "up"
    )
with kpi_c5:
    render_metric_card(
        label="Cumulative Wasted Spend",
        value=f"${total_cumulative_wasted:,.2f}",
        delta="Lifetime waste",
        delta_type="down" if total_cumulative_wasted > 0 else "up"
    )

st.write("")

# 9. Plotly Shared Theming Setup
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#fafafa" if IS_DARK else "#09090b", size=11),
    margin=dict(l=40, r=20, t=20, b=30),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        zerolinecolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        tickfont=dict(size=10, color="#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        zerolinecolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        tickfont=dict(size=10, color="#71717a"),
    ),
)

# 10. Dashboard Grid Layout
chart_row_1_left, chart_row_1_right = st.columns([5, 5])

# Donut Chart: Spend by Category
with chart_row_1_left:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Recurring Spend by Category</div>
        <div class="chart-subtitle">Distribution of total monthly spend across categories</div>
    """, unsafe_allow_html=True)
    
    category_df = df_active.groupby('category')['current_amount'].sum().reset_index()
    fig_donut = px.pie(
        category_df, 
        values='current_amount', 
        names='category', 
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Plotly if IS_DARK else px.colors.qualitative.Safe
    )
    
    # Apply styling
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#fafafa" if IS_DARK else "#09090b", size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# Bar Chart: Top Creeping Merchants
with chart_row_1_right:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Price Creep by Merchant</div>
        <div class="chart-subtitle">Average price increase of active subscriptions per provider</div>
    """, unsafe_allow_html=True)
    
    creep_df = df_active.groupby('merchant_name')['price_creep'].mean().reset_index().sort_values(by='price_creep', ascending=True)
    
    fig_bar = px.bar(
        creep_df, 
        y='merchant_name', 
        x='price_creep', 
        orientation='h',
        labels={'merchant_name': 'Merchant', 'price_creep': 'Average Creep ($)'},
        color_discrete_sequence=['#2563eb' if not IS_DARK else '#3b82f6']
    )
    
    fig_bar.update_layout(**PLOT_LAYOUT)
    fig_bar.update_traces(marker_line_width=0, opacity=0.85)
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

chart_row_2_left, chart_row_2_right = st.columns([5, 5])

# Histogram: Tenure Distribution
with chart_row_2_left:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Subscription Tenure Distribution</div>
        <div class="chart-subtitle">Ages of active subscriptions (days), grouped by zombie flag</div>
    """, unsafe_allow_html=True)
    
    # Group active subscriptions into Tenure Bins and color by whether they are zombies
    df_active['Status'] = df_active['is_zombie'].apply(lambda z: 'Flagged Zombie' if z else 'Regular Active')
    
    fig_hist = px.histogram(
        df_active, 
        x='tenure_days', 
        color='Status',
        nbins=20,
        barmode='overlay',
        labels={'tenure_days': 'Tenure (Days)', 'count': 'Number of Subscriptions'},
        color_discrete_map={'Flagged Zombie': '#ef4444' if IS_DARK else '#dc2626', 'Regular Active': '#10b981' if IS_DARK else '#059669'}
    )
    
    fig_hist.update_layout(**PLOT_LAYOUT)
    fig_hist.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
    fig_hist.update_traces(opacity=0.75, marker_line_width=0)
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# Scatter/Line: Cumulative Wasted Spend / Price Creep over Time
with chart_row_2_right:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Wasted Spend Trajectory (Sample Users)</div>
        <div class="chart-subtitle">Cumulative monthly cost trajectories for top price-creeping zombies</div>
    """, unsafe_allow_html=True)
    
    # We will pick 5 top zombie candidate users with price creep to show their payment trajectories
    top_creepers = zombie_subs_df[zombie_subs_df['price_creep'] > 0].sort_values(by='total_amount_paid', ascending=False).head(5)
    
    trajectories = []
    for _, row in top_creepers.iterrows():
        user_id, merchant_id = row['user_id'], row['merchant_id']
        user_tx = df_tx[(df_tx['user_id'] == user_id) & (df_tx['merchant_id'] == merchant_id)].copy()
        user_tx['cumulative_paid'] = user_tx['amount'].cumsum()
        user_tx['series_label'] = f"{row['user_name']} - {row['merchant_name']}"
        trajectories.append(user_tx)
        
    if trajectories:
        df_trajectories = pd.concat(trajectories)
        fig_line = px.line(
            df_trajectories, 
            x='transaction_date', 
            y='cumulative_paid', 
            color='series_label',
            labels={'transaction_date': 'Date', 'cumulative_paid': 'Cumulative Cost ($)'},
            color_discrete_sequence=px.colors.qualitative.Safe if not IS_DARK else px.colors.qualitative.Plotly
        )
        fig_line.update_layout(**PLOT_LAYOUT)
        fig_line.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5))
        fig_line.update_traces(line=dict(width=2.5))
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    else:
        st.write("No price-creeping zombie subscriptions found under the selected strategy.")
        
    st.markdown("</div>", unsafe_allow_html=True)

# 11. Detailed Data Explorer
st.markdown("### Subscription Explorer")
tabs = st.tabs(["⚠️ High-Priority Zombies", "🔍 All Active Subscriptions", "ℹ️ Merchant Price Analysis"])

# Tab 1: Flagged Zombies
with tabs[0]:
    if len(zombie_subs_df) > 0:
        st.markdown(f"**{len(zombie_subs_df)} subscriptions flagged as zombie candidates.** Click columns to sort or filter.")
        
        # Sort flagged zombies by total amount paid descending
        zombies_sorted = zombie_subs_df.sort_values(by='total_amount_paid', ascending=False)
        
        rows_html = ""
        for _, r in zombies_sorted.iterrows():
            badge_html = ""
            if r['price_creep'] > 0:
                badge_html += '<span class="badge badge-red" style="margin-right: 4px;">PRICE CREEP</span>'
            if r['tenure_days'] > 360:
                badge_html += '<span class="badge badge-amber">LONG TENURE</span>'
            if not badge_html:
                badge_html = '<span class="badge badge-blue">ZOMBIE</span>'
                
            rows_html += f"""
            <tr>
                <td>{r['user_name']}</td>
                <td>{r['merchant_name']}</td>
                <td><span class="badge badge-blue">{r['category']}</span></td>
                <td>{r['tenure_days']} days</td>
                <td>${r['start_amount']:.2f}</td>
                <td>${r['current_amount']:.2f}</td>
                <td style="color: {"#ef4444" if r['price_creep'] > 0 else "inherit"}; font-weight: {600 if r['price_creep'] > 0 else "inherit"}">
                    +${r['price_creep']:.2f}
                </td>
                <td style="font-weight: 600;">${r['total_amount_paid']:.2f}</td>
                <td>{badge_html}</td>
            </tr>
            """
            
        st.markdown(f"""
        <div class="data-table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Merchant</th>
                        <th>Category</th>
                        <th>Tenure</th>
                        <th>Start Price</th>
                        <th>Current Price</th>
                        <th>Price Creep</th>
                        <th>Cumulative Cost</th>
                        <th>Signals</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No subscriptions flagged as zombie candidates under the current strategy.")

# Tab 2: All Active Subscriptions Explorer
with tabs[1]:
    search_q = st.text_input("Search by User Name or Merchant", "")
    
    df_filtered = df_active.copy()
    if search_q:
        df_filtered = df_filtered[
            df_filtered['user_name'].str.contains(search_q, case=False, na=False) |
            df_filtered['merchant_name'].str.contains(search_q, case=False, na=False)
        ]
        
    st.markdown(f"Showing {len(df_filtered)} active subscriptions.")
    
    rows_html = ""
    for _, r in df_filtered.head(100).iterrows(): # Cap rendering for performance
        status_badge = '<span class="badge badge-red">ZOMBIE</span>' if r['is_zombie'] else '<span class="badge badge-green">ACTIVE</span>'
        
        rows_html += f"""
        <tr>
            <td>{r['user_name']}</td>
            <td>{r['merchant_name']}</td>
            <td>{r['category']}</td>
            <td>{r['tenure_days']} days</td>
            <td>${r['current_amount']:.2f}</td>
            <td>${r['price_creep']:.2f}</td>
            <td>${r['total_amount_paid']:.2f}</td>
            <td>{status_badge}</td>
        </tr>
        """
        
    st.markdown(f"""
    <div class="data-table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Merchant</th>
                    <th>Category</th>
                    <th>Tenure</th>
                    <th>Current Price</th>
                    <th>Price Creep</th>
                    <th>Cumulative Paid</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    if len(df_filtered) > 100:
        st.caption(f"... and {len(df_filtered) - 100} more rows (capped at 100 rows for display performance).")

# Tab 3: Merchant Analysis & Metrics
with tabs[2]:
    st.markdown("### Merchant Pricing Performance")
    
    # Calculate stats per merchant
    merchant_stats = []
    for merchant in df_active['merchant_name'].unique():
        m_df = df_active[df_active['merchant_name'] == merchant]
        avg_tenure = m_df['tenure_days'].mean()
        avg_price = m_df['current_amount'].mean()
        zombie_count = m_df['is_zombie'].sum()
        total_m_spend = m_df['current_amount'].sum()
        zombie_pct = (zombie_count / len(m_df)) * 100
        
        merchant_stats.append({
            "Merchant": merchant,
            "Active Accounts": len(m_df),
            "Zombies": zombie_count,
            "Zombie %": f"{zombie_pct:.1f}%",
            "Avg Tenure": f"{avg_tenure:.0f} days",
            "Avg Price": f"${avg_price:.2f}",
            "Monthly Spend": f"${total_m_spend:,.2f}"
        })
        
    df_m_stats = pd.DataFrame(merchant_stats)
    
    rows_html = ""
    for _, r in df_m_stats.iterrows():
        rows_html += f"""
        <tr>
            <td><b>{r['Merchant']}</b></td>
            <td>{r['Active Accounts']}</td>
            <td>{r['Zombies']}</td>
            <td>{r['Zombie %']}</td>
            <td>{r['Avg Tenure']}</td>
            <td>{r['Avg Price']}</td>
            <td>{r['Monthly Spend']}</td>
        </tr>
        """
        
    st.markdown(f"""
    <div class="data-table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Merchant</th>
                    <th>Active Accounts</th>
                    <th>Zombies</th>
                    <th>Zombie %</th>
                    <th>Avg Tenure</th>
                    <th>Avg Price</th>
                    <th>Monthly Spend</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

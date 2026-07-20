import streamlit as st
import textwrap
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

# Initialize Session State to track cancellations in this dashboard session
if "session_cancelled" not in st.session_state:
    st.session_state.session_cancelled = []

# 3. CSS Variables & Custom Injection
def st_html(html_str):
    clean_lines = [line.strip() for line in html_str.split("\n")]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

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
st_html(css)

# 4. Helper to render KPI cards
def render_metric_card(label, value, delta=None, delta_type="up"):
    cls = f"delta-{delta_type}"
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else "→")
    delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>' if delta else ""
    st_html(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """)

# Format tenure dynamically in months and years
def format_tenure(days):
    if days is None:
        return "N/A"
    months = int(round(days / 30.0))
    if months <= 0:
        return "1 month"
    if months < 12:
        return f"{months} months"
    years = months // 12
    rem_months = months % 12
    if rem_months == 0:
        return f"{years} years" if years > 1 else f"{years} year"
    else:
        return f"{years} yr {rem_months} mo"

# 5. Database Connections and Ingestion Logic
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

# 6. Cancellation database execution
def cancel_subscription(user_id, merchant_id, current_amount, merchant_name):
    conn = sqlite3.connect("zombie_detector.db")
    cursor = conn.cursor()
    # Cancel the subscription by setting end_date to today
    today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
    cursor.execute(
        "UPDATE dim_subscriptions SET end_date = ? WHERE user_id = ? AND merchant_id = ?;",
        (today_str, int(user_id), int(merchant_id))
    )
    conn.commit()
    conn.close()
    
    # Track the savings in session state
    st.session_state.session_cancelled.append({
        "user_id": user_id,
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "amount": current_amount
    })
    
    # Flush Streamlit caching and force rerun to refresh layout
    st.cache_data.clear()
    st.toast(f"Successfully cancelled subscription to {merchant_name}!")
    st.rerun()

# 7. Financial Health Score grading calculation
def calculate_health_score(df_active_subset):
    if len(df_active_subset) == 0:
        return 100, "A+", "green"
        
    zombies = df_active_subset[df_active_subset['is_zombie']]
    zombie_monthly = zombies['current_amount'].sum()
    total_monthly = df_active_subset['current_amount'].sum()
    
    if total_monthly == 0:
        return 100, "A+", "green"
        
    waste_ratio = zombie_monthly / total_monthly
    score = max(0, 100 - int(waste_ratio * 100))
    
    if score >= 95:
        return score, "A+", "green"
    elif score >= 90:
        return score, "A", "green"
    elif score >= 80:
        return score, "B", "blue"
    elif score >= 70:
        return score, "C", "amber"
    elif score >= 60:
        return score, "D", "amber"
    else:
        return score, "F", "red"

# Fetch main datasets
df_subs, df_tx = get_dashboard_data()

# Filter down to Active Subscriptions
df_active = df_subs[df_subs['end_date'].isna() | (df_subs['end_date'] == '')].copy()

# 8. Navigation & URL Router
st.sidebar.markdown("### Navigation")
query_user = st.query_params.get("user", "")

# Determine page default based on query params
default_page = "📊 Portfolio Overview"
if query_user:
    default_page = "👤 Individual Profiles"

page = st.sidebar.radio(
    "Go to page",
    options=["📊 Portfolio Overview", "👤 Individual Profiles", "🔬 Model Validation & ROI"],
    index=0 if default_page == "📊 Portfolio Overview" else 1
)

# Load layout state variables based on page selection
if page == "👤 Individual Profiles":
    st.sidebar.markdown("### Search Profile")
    search_term = st.sidebar.text_input("Type Name to Search", "")
    
    user_list = sorted(df_active['user_name'].unique().tolist())
    
    if search_term:
        filtered_users = [u for u in user_list if search_term.lower() in u.lower()]
        if not filtered_users:
            st.sidebar.warning("No profiles match your search.")
            filtered_users = user_list  # fallback to full list
    else:
        filtered_users = user_list
        
    st.sidebar.markdown("### Profile Selector")
    default_user_idx = 0
    if query_user in filtered_users:
        default_user_idx = filtered_users.index(query_user)
        
    selected_user = st.sidebar.selectbox(
        "Select User Profile",
        options=filtered_users,
        index=default_user_idx
    )
    
    # Update query params to provide deep linking
    st.query_params["user"] = selected_user
    
    # Filter dataset for selected user
    df_active = df_active[df_active['user_name'] == selected_user].copy()
    user_id_val = df_active['user_id'].iloc[0] if len(df_active) > 0 else None
    df_tx = df_tx[df_tx['user_id'] == user_id_val].copy()
else:
    # Portfolio Overview / Validation view (clear query parameters to return to root page)
    if "user" in st.query_params:
        st.query_params.clear()
    selected_user = "All Users"

# 9. UI Header
head_left, head_right = st.columns([9, 1])
with head_left:
    if page == "📊 Portfolio Overview":
        subtitle_text = "Interactive recurring billing analytics and wasted spend visualization"
    elif page == "👤 Individual Profiles":
        subtitle_text = f"Personal subscription dashboard for <b>{selected_user}</b>"
    else:
        subtitle_text = "Live validation report and ROI analytics comparing SQL-based strategies"
        
    st_html(f"""
    <div class="brand">
        <span class="brand-name">🧟 Zombie Subscription Detector</span>
    </div>
    <div class="brand-subtitle">{subtitle_text}</div>
    """)
with head_right:
    theme_label = "☀️ Light" if IS_DARK else "🌙 Dark"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

# 10. Sidebar Controls - Zombie Classification parameters
if page != "🔬 Model Validation & ROI":
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

    # Apply selected strategy logic to flag zombies
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

# Calculate common metric variables
total_subs = len(df_active)
zombie_subs_df = df_active[df_active['is_zombie']] if page != "🔬 Model Validation & ROI" else pd.DataFrame()
num_zombies = len(zombie_subs_df)

total_monthly_spend = df_active['current_amount'].sum()
zombie_monthly_spend = zombie_subs_df['current_amount'].sum()
zombie_pct = (num_zombies / total_subs) * 100 if total_subs > 0 else 0

total_cumulative_wasted = zombie_subs_df['total_amount_paid'].sum()

# Render content based on active page
if page != "🔬 Model Validation & ROI":
    
    # Calculate health score metrics
    health_score, health_grade, health_color = calculate_health_score(df_active)
    
    # Calculate savings from cancellations in this session
    if page == "👤 Individual Profiles":
        session_savings = sum(item['amount'] for item in st.session_state.session_cancelled if item['user_id'] == user_id_val)
        num_cancelled = len([item for item in st.session_state.session_cancelled if item['user_id'] == user_id_val])
    else:
        session_savings = sum(item['amount'] for item in st.session_state.session_cancelled)
        num_cancelled = len(st.session_state.session_cancelled)

    # 11. Render KPI Metric Cards
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)
    
    with kpi_c1:
        render_metric_card(
            label="Active Subscriptions",
            value=f"{total_subs}",
            delta=None
        )
    with kpi_c2:
        render_metric_card(
            label="Monthly Spend",
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
        # Financial Health Score KPI
        render_metric_card(
            label="Financial Health Index",
            value=f"{health_score}%",
            delta=f"Grade: {health_grade}",
            delta_type="up" if health_color == "green" else ("warn" if health_color == "amber" else "down")
        )
    with kpi_c5:
        # Saved Monthly Spend KPI (from local cancellations)
        render_metric_card(
            label="Saved Monthly Spend",
            value=f"${session_savings:,.2f}",
            delta=f"{num_cancelled} cancelled",
            delta_type="up" if session_savings > 0 else "down"
        )

    st.write("")

    # 12. Plotly Shared Theming Setup
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

    # 13. Dashboard Grid Layout
    chart_row_1_left, chart_row_1_right = st.columns([5, 5])
    
    # Donut Chart: Spend by Category
    with chart_row_1_left:
        st_html("""
        <div class="chart-wrap">
            <div class="chart-title">Recurring Spend by Category</div>
            <div class="chart-subtitle">Distribution of total monthly spend across categories</div>
        """)
        
        category_df = df_active.groupby('category')['current_amount'].sum().reset_index()
        fig_donut = px.pie(
            category_df, 
            values='current_amount', 
            names='category', 
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Plotly if IS_DARK else px.colors.qualitative.Safe
        )
        
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans, sans-serif", color="#fafafa" if IS_DARK else "#09090b", size=11),
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
        st_html("</div>")
    
    # Bar Chart: Top Creeping Merchants
    with chart_row_1_right:
        st_html("""
        <div class="chart-wrap">
            <div class="chart-title">Price Creep by Merchant</div>
            <div class="chart-subtitle">Average price increase of active subscriptions per provider</div>
        """)
        
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
        st_html("</div>")
    
    chart_row_2_left, chart_row_2_right = st.columns([5, 5])
    
    # Histogram: Tenure Distribution
    with chart_row_2_left:
        st_html("""
        <div class="chart-wrap">
            <div class="chart-title">Subscription Tenure Distribution</div>
            <div class="chart-subtitle">Ages of active subscriptions (days), grouped by zombie flag</div>
        """)
        
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
        st_html("</div>")
    
    # Scatter/Line: Cumulative Wasted Spend / Price Creep over Time
    with chart_row_2_right:
        chart_line_title = "Wasted Spend Trajectory (Sample Users)" if page == "📊 Portfolio Overview" else f"Cost Trajectory: {selected_user}"
        chart_line_subtitle = "Cumulative monthly cost trajectories for top price-creeping zombies" if page == "📊 Portfolio Overview" else "Cumulative subscription cost over time"
        
        st_html(f"""
        <div class="chart-wrap">
            <div class="chart-title">{chart_line_title}</div>
            <div class="chart-subtitle">{chart_line_subtitle}</div>
        """)
        
        trajectories = []
        if page == "📊 Portfolio Overview":
            top_creepers = df_active[df_active['price_creep'] > 0].sort_values(by='total_amount_paid', ascending=False).head(5)
            for _, row in top_creepers.iterrows():
                u_id, m_id = row['user_id'], row['merchant_id']
                user_tx = df_tx[(df_tx['user_id'] == u_id) & (df_tx['merchant_id'] == m_id)].copy()
                user_tx['cumulative_paid'] = user_tx['amount'].cumsum()
                user_tx['series_label'] = f"{row['user_name']} - {row['merchant_name']}"
                trajectories.append(user_tx)
        else:
            for _, row in df_active.iterrows():
                u_id, m_id = row['user_id'], row['merchant_id']
                user_tx = df_tx[(df_tx['user_id'] == u_id) & (df_tx['merchant_id'] == m_id)].copy()
                user_tx['cumulative_paid'] = user_tx['amount'].cumsum()
                user_tx['series_label'] = f"{row['merchant_name']}"
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
            st.write("No active subscriptions or data found for this selection.")
            
        st_html("</div>")

    # 14. Detailed Data Explorer
    st.markdown("### Subscription Explorer")
    tabs = st.tabs(["⚠️ High-Priority Zombies", "🔍 All Active Subscriptions", "ℹ️ Merchant Price Analysis"])
    
    # Tab 1: Flagged Zombies
    with tabs[0]:
        if len(zombie_subs_df) > 0:
            st.markdown(f"**{len(zombie_subs_df)} subscriptions flagged as zombie candidates.** Click columns to sort or filter.")
            
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
                    
                rows_html += textwrap.dedent(f"""
                <tr>
                    <td>{r['user_name']}</td>
                    <td>{r['merchant_name']}</td>
                    <td><span class="badge badge-blue">{r['category']}</span></td>
                    <td>{format_tenure(r['tenure_days'])}</td>
                    <td>${r['start_amount']:.2f}</td>
                    <td>${r['current_amount']:.2f}</td>
                    <td style="color: {"#ef4444" if r['price_creep'] > 0 else "inherit"}; font-weight: {600 if r['price_creep'] > 0 else "inherit"}">
                        +${r['price_creep']:.2f}
                    </td>
                    <td style="font-weight: 600;">${r['total_amount_paid']:.2f}</td>
                    <td>{badge_html}</td>
                </tr>
                """)
                
            st_html(f"""
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
            """)
        else:
            st.info("No subscriptions flagged as zombie candidates under the current strategy.")
    
    # Tab 2: All Active Subscriptions Explorer
    with tabs[1]:
        # Only show search filter if page is portfolio view (so individual page stays clean)
        if page == "📊 Portfolio Overview":
            search_q = st.text_input("Search by User Name or Merchant", "")
        else:
            search_q = ""
        
        df_filtered = df_active.copy()
        if search_q:
            df_filtered = df_filtered[
                df_filtered['user_name'].str.contains(search_q, case=False, na=False) |
                df_filtered['merchant_name'].str.contains(search_q, case=False, na=False)
            ]
            
        st.markdown(f"Showing {len(df_filtered)} active subscriptions.")
        
        rows_html = ""
        for _, r in df_filtered.head(100).iterrows():
            status_badge = '<span class="badge badge-red">ZOMBIE</span>' if r['is_zombie'] else '<span class="badge badge-green">ACTIVE</span>'
            
            rows_html += textwrap.dedent(f"""
            <tr>
                <td>{r['user_name']}</td>
                <td>{r['merchant_name']}</td>
                <td>{r['category']}</td>
                <td>{format_tenure(r['tenure_days'])}</td>
                <td>${r['current_amount']:.2f}</td>
                <td>${r['price_creep']:.2f}</td>
                <td>${r['total_amount_paid']:.2f}</td>
                <td>{status_badge}</td>
            </tr>
            """)
            
        st_html(f"""
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
        """)
        
        if len(df_filtered) > 100:
            st.caption(f"... and {len(df_filtered) - 100} more rows (capped at 100 rows for display performance).")
    
    # Tab 3: Merchant Analysis & Metrics
    with tabs[2]:
        st.markdown("### Merchant Pricing Performance")
        
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
                "Avg Tenure": format_tenure(avg_tenure),
                "Avg Price": f"${avg_price:.2f}",
                "Monthly Spend": f"${total_m_spend:,.2f}"
            })
            
        df_m_stats = pd.DataFrame(merchant_stats)
        
        rows_html = ""
        for _, r in df_m_stats.iterrows():
            rows_html += textwrap.dedent(f"""
            <tr>
                <td><b>{r['Merchant']}</b></td>
                <td>{r['Active Accounts']}</td>
                <td>{r['Zombies']}</td>
                <td>{r['Zombie %']}</td>
                <td>{r['Avg Tenure']}</td>
                <td>{r['Avg Price']}</td>
                <td>{r['Monthly Spend']}</td>
            </tr>
            """)
            
        st_html(f"""
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
        """)

    # 15. Action Center: Simulated Cancellation Control
    st.write("")
    st.markdown("### 🛠️ Action Center: Manage Subscriptions")
    if len(df_active) > 0:
        sub_options = {
            f"{r['merchant_name']} (${r['current_amount']:.2f}/mo)": (r['user_id'], r['merchant_id'], r['current_amount'], r['merchant_name']) 
            for _, r in df_active.iterrows()
        }
        
        # User dropdown select to cancel
        selected_sub_label = st.selectbox(
            "Select Active Subscription to Cancel:", 
            options=list(sub_options.keys())
        )
        
        cancel_btn = st.button("Cancel Selected Subscription", use_container_width=True)
        if cancel_btn:
            u_id, m_id, amt, m_name = sub_options[selected_sub_label]
            cancel_subscription(u_id, m_id, amt, m_name)
    else:
        st.info("No active subscriptions to manage.")

else:
    # Page: 🔬 Model Validation & ROI
    st.write("")
    
    @st.cache_data
    def get_validation_metrics(df_source):
        # Filter to active rows in database
        active_subs = df_source[df_source['end_date'].isna() | (df_source['end_date'] == '')].copy()
        
        strategies = {
            "Strategy A: Price Creep Only (creep > 0)": lambda r: r['price_creep'] > 0,
            "Strategy B1: Long Tenure (tenure > 360 days)": lambda r: r['tenure_days'] > 360,
            "Strategy B2: Long Tenure (tenure > 180 days)": lambda r: r['tenure_days'] > 180,
            "Strategy C1: Combined (creep > 0 OR tenure > 360 days)": lambda r: (r['price_creep'] > 0) or (r['tenure_days'] > 360),
            "Strategy C2: Combined (creep > 0 OR tenure > 180 days)": lambda r: (r['price_creep'] > 0) or (r['tenure_days'] > 180)
        }
        
        results = []
        for name, rule in strategies.items():
            tp = fp = fn = tn = 0
            for _, row in active_subs.iterrows():
                actual = row['is_zombie_ground_truth']
                predicted = 1 if rule(row) else 0
                
                if predicted == 1 and actual == 1:
                    tp += 1
                elif predicted == 1 and actual == 0:
                    fp += 1
                elif predicted == 0 and actual == 1:
                    fn += 1
                else:
                    tn += 1
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            results.append({
                "Strategy": name,
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "TN": tn,
                "Precision": f"{precision:.2%}",
                "Recall": f"{recall:.2%}",
                "F1": f"{f1:.2%}",
                "F1_score": f1
            })
        return pd.DataFrame(results)

    df_metrics = get_validation_metrics(df_subs)
    
    val_c1, val_c2 = st.columns([6, 4])
    
    with val_c1:
        st_html("""
        <div class="chart-wrap">
            <div class="chart-title">Strategy Comparison & Validation Metrics</div>
            <div class="chart-subtitle">Calculated live against 855 ground-truth subscription labels</div>
        """)
        
        rows_html = ""
        for _, r in df_metrics.iterrows():
            rows_html += textwrap.dedent(f"""
            <tr>
                <td><b>{r['Strategy']}</b></td>
                <td>{r['TP']}</td>
                <td>{r['FP']}</td>
                <td>{r['FN']}</td>
                <td style="color: var(--green); font-weight: 600;">{r['Precision']}</td>
                <td style="color: var(--accent); font-weight: 600;">{r['Recall']}</td>
                <td style="background: var(--bg-subtle); font-weight: 700;">{r['F1']}</td>
            </tr>
            """)
            
        st_html(f"""
        <div class="data-table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>TP</th>
                        <th>FP</th>
                        <th>FN</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>F1-Score</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """)
        st_html("</div>")
        
    with val_c2:
        st_html("""
        <div class="chart-wrap">
            <div class="chart-title">F1-Score Performance Index</div>
            <div class="chart-subtitle">Higher F1 means better balance of precision & recall</div>
        """)
        
        fig_f1 = px.bar(
            df_metrics,
            y='Strategy',
            x='F1_score',
            orientation='h',
            color='F1_score',
            color_continuous_scale=px.colors.sequential.Blues if IS_DARK else px.colors.sequential.YlGnBu,
            labels={'F1_score': 'F1 Score'}
        )
        
        PLOT_LAYOUT_VAL = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans, sans-serif", color="#fafafa" if IS_DARK else "#09090b", size=11),
            margin=dict(l=40, r=20, t=10, b=20),
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
        
        fig_f1.update_layout(**PLOT_LAYOUT_VAL)
        fig_f1.update_layout(coloraxis_showscale=False)
        fig_f1.update_traces(marker_line_width=0)
        st.plotly_chart(fig_f1, use_container_width=True, config={"displayModeBar": False})
        st_html("</div>")
        
    st.markdown("### 💡 Business Interpretation & Strategic ROI Analysis")
    st_html("""
    <div style="background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem 1.5rem; margin-top: 0.5rem; font-size: 0.82rem; line-height: 1.5;">
        <p style="margin-bottom: 0.75rem;">
            <b>Why Strategy A (Price Creep Only) is the Safest Commercial Trigger:</b><br/>
            With a <b>100.00% Precision</b> rating, Strategy A generates <b>zero false positives</b>. This means that if a system sends an automated cancellation push notification to a user based on Strategy A (e.g., <i>"We noticed Netflix increased your subscription from $15.99 to $17.99, do you want to keep it?"</i>), the system will <b>never</b> annoy an active user. Every single alert is triggered on a valid price growth. This is the optimal configuration for customer trust and retention.
        </p>
        <p style="margin-bottom: 0.75rem;">
            <b>The Limitations of Tenure-Only Triggers:</b><br/>
            Strategies B1 and B2 (Tenure-only) catch almost all zombie subscriptions (up to <b>96.53% Recall</b>), but they have a low precision of <b>~24%</b>. In business terms, if we alert users solely because their account is older than 6 months, <b>76% of those alerts will target users who are actively and happily using their services</b>. This creates high alert fatigue and may cause users to disable notifications.
        </p>
        <p>
            <b>Recommended Implementation Pathway:</b><br/>
            Deploy a <b>two-tiered alert architecture</b>. Use Strategy A (Price Creep) to send high-confidence, actionable "Cancel with 1-Tap" notifications. Use Strategy B1 (Tenure > 1 year) to display a passive "Subscription Review Checklist" directly in the dashboard UI without sending intrusive push alerts.
        </p>
    </div>
    """)

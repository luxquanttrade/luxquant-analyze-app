"""
LuxQuant Pro - Fixed Version
Professional Trading Signals Analytics Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="LuxQuant Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme colors
COLORS = {
    "background": "#0E1117",
    "card_bg": "#1A1D24",
    "green": "#00D46A",
    "red": "#FF4747",
    "yellow": "#FDB32B",
    "blue": "#4B9BFF",
    "purple": "#9D5CFF",
    "text_muted": "#6B6B6B"
}

# Custom CSS for dark theme
st.markdown("""
<style>
.stApp { background-color: #0E1117; }
[data-testid="metric-container"] {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    # Import modules
    try:
        from database.connection import get_connection_status, load_data
        from data_processing.signal_processor import process_signals
        from utils.helpers import apply_filters
    except ImportError as e:
        st.error(f"Import Error: {e}")
        st.info("Please ensure all module files are in place")
        return
    
    # Header
    render_header()
    
    # Check connection
    conn_status = get_connection_status()
    
    # Sidebar
    filters = render_sidebar()
    
    if not conn_status.get("connected"):
        st.error("❌ Database connection failed")
        st.code(conn_status.get('error', 'Unknown error'))
        return
    
    # Load and process data
    try:
        # Load data
        with st.spinner("Loading data..."):
            raw_data = load_data()
        
        if not raw_data or 'signals' not in raw_data:
            st.error("No data loaded from database")
            return
        
        # Process signals
        with st.spinner("Processing signals..."):
            processed_data = process_signals(raw_data)
        
        if processed_data is None or processed_data.empty:
            st.warning("No data after processing")
            return
        
        # Apply filters
        filtered_data = apply_filters(processed_data, filters)
        
        # Render dashboard
        render_dashboard(filtered_data)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)

def render_header():
    """Render header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">LuxQuant Pro</h1>
        <p style="color: #A0A0A0;">Professional Trading Signals Analytics Dashboard</p>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: right; padding-top: 20px;">
            <span style="color: #00D46A;">● Live</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"""
        <div style="text-align: right; padding-top: 20px;">
            <span style="color: #A0A0A0;">{current_time} UTC</span>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with filters"""
    st.sidebar.title("Filters")
    
    filters = {}
    filters['date_from'] = st.sidebar.date_input("From Date", value=None)
    filters['date_to'] = st.sidebar.date_input("To Date", value=None)
    filters['pair_filter'] = st.sidebar.text_input("Pairs (comma-separated)")
    filters['auto_load'] = True
    
    return filters

def render_dashboard(data):
    """Render main dashboard"""
    if data is None or data.empty:
        st.warning("No data available")
        return
    
    # Calculate metrics
    metrics = calculate_metrics(data)
    
    # 1. Win Rate Trend
    st.subheader("📈 Win Rate Trend Analysis")
    render_winrate_chart(data)
    
    # 2. Summary Cards
    st.subheader("📊 Performance Overview")
    render_metric_cards(metrics)
    
    # 3. Top Performers
    st.subheader("🏆 Top Performers")
    render_top_performers(data)

def calculate_metrics(data):
    """Calculate summary metrics"""
    metrics = {}
    
    # Basic counts
    metrics['total_signals'] = len(data)
    metrics['closed_trades'] = data['final_outcome'].notna().sum() if 'final_outcome' in data.columns else 0
    metrics['open_signals'] = metrics['total_signals'] - metrics['closed_trades']
    
    # Win rate
    if metrics['closed_trades'] > 0 and 'final_outcome' in data.columns:
        tp_hits = data['final_outcome'].str.startswith('tp', na=False).sum()
        metrics['tp_hits'] = tp_hits
        metrics['sl_hits'] = (data['final_outcome'] == 'sl').sum()
        metrics['win_rate'] = (tp_hits / metrics['closed_trades'] * 100)
    else:
        metrics['tp_hits'] = 0
        metrics['sl_hits'] = 0
        metrics['win_rate'] = 0
    
    # Completion rate
    metrics['completion_rate'] = (metrics['closed_trades'] / metrics['total_signals'] * 100) if metrics['total_signals'] > 0 else 0
    
    # RR metrics
    if 'rr_planned' in data.columns:
        rr_data = data['rr_planned'].dropna()
        metrics['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
    else:
        metrics['avg_rr'] = 0
    
    # Pairs
    if 'pair' in data.columns:
        metrics['active_pairs'] = data['pair'].nunique()
        metrics['top_pair'] = data['pair'].value_counts().index[0] if not data['pair'].empty else "N/A"
    else:
        metrics['active_pairs'] = 0
        metrics['top_pair'] = "N/A"
    
    return metrics

def render_metric_cards(metrics):
    """Render metric cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Signals",
            f"{metrics['total_signals']:,}",
            f"Active: {metrics['active_pairs']} pairs"
        )
    
    with col2:
        st.metric(
            "Win Rate",
            f"{metrics['win_rate']:.1f}%",
            "Overall performance"
        )
    
    with col3:
        st.metric(
            "Completion Rate",
            f"{metrics['completion_rate']:.1f}%",
            f"{metrics['closed_trades']} closed"
        )
    
    with col4:
        st.metric(
            "Avg RR Ratio",
            f"{metrics['avg_rr']:.2f}",
            "Risk-Reward"
        )
    
    # Second row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("TP Hits", f"{metrics['tp_hits']:,}")
    
    with col2:
        st.metric("SL Hits", f"{metrics['sl_hits']:,}")
    
    with col3:
        st.metric("Open Signals", f"{metrics['open_signals']:,}")
    
    with col4:
        st.metric("Top Pair", metrics['top_pair'])

def render_winrate_chart(data):
    """Render winrate trend chart"""
    if 'created_at' not in data.columns or 'final_outcome' not in data.columns:
        st.info("Not enough data for trend analysis")
        return
    
    # Calculate winrate by date
    closed_data = data[data['final_outcome'].notna()].copy()
    if closed_data.empty:
        st.info("No closed trades for analysis")
        return
    
    # Parse dates safely
    closed_data['date'] = pd.to_datetime(closed_data['created_at'], errors='coerce').dt.date
    closed_data = closed_data[closed_data['date'].notna()]
    
    if closed_data.empty:
        st.info("No valid date data")
        return
    
    closed_data['is_winner'] = closed_data['final_outcome'].str.startswith('tp', na=False)
    
    # Group by date
    daily_stats = closed_data.groupby('date').agg({
        'is_winner': ['sum', 'count']
    }).reset_index()
    
    daily_stats.columns = ['date', 'wins', 'total']
    daily_stats['winrate'] = (daily_stats['wins'] / daily_stats['total'] * 100)
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_stats['date'],
        y=daily_stats['winrate'],
        mode='lines+markers',
        name='Win Rate',
        line=dict(color=COLORS['green'], width=3),
        marker=dict(size=8, color=COLORS['green']),
        fill='tonexty',
        fillcolor='rgba(0, 212, 106, 0.1)'
    ))
    
    # Add 50% line
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color=COLORS['text_muted'],
        opacity=0.5,
        annotation_text="Break Even"
    )
    
    fig.update_layout(
        title=None,
        xaxis_title="Date",
        yaxis_title="Win Rate (%)",
        height=350,
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#1A1D24",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_top_performers(data):
    """Render top performers section"""
    if 'pair' not in data.columns:
        st.info("No pair data available")
        return
    
    # Calculate pair metrics
    pair_stats = []
    for pair in data['pair'].unique():
        pair_data = data[data['pair'] == pair]
        
        stats = {
            'pair': pair,
            'signals': len(pair_data),
            'closed': pair_data['final_outcome'].notna().sum() if 'final_outcome' in pair_data.columns else 0
        }
        
        if stats['closed'] > 0 and 'final_outcome' in pair_data.columns:
            tp_hits = pair_data['final_outcome'].str.startswith('tp', na=False).sum()
            stats['win_rate'] = (tp_hits / stats['closed'] * 100)
        else:
            stats['win_rate'] = 0
        
        pair_stats.append(stats)
    
    pair_df = pd.DataFrame(pair_stats)
    
    # Filter and sort
    qualified = pair_df[pair_df['signals'] >= 3].nlargest(20, 'win_rate')
    
    if qualified.empty:
        st.info("Not enough data for top performers")
        return
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=qualified['pair'][:10][::-1],
        x=qualified['win_rate'][:10][::-1],
        orientation='h',
        marker=dict(color=COLORS['green']),
        text=[f"{wr:.1f}%" for wr in qualified['win_rate'][:10][::-1]],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Top 10 Pairs by Win Rate",
        xaxis_title="Win Rate (%)",
        yaxis_title="",
        height=400,
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#1A1D24"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show table
    st.dataframe(
        qualified[['pair', 'signals', 'win_rate']].head(10),
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()
"""
🏠 Home - LuxQuant Pro
Enhanced Version - Professional Trading Signals Analytics Dashboard with Time Range Support
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
    page_title="🏠 Home - LuxQuant Dashboard Performance",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme colors
# Dark theme colors - LuxQuant Style
COLORS = {
    "background": "#000000",           # Pure black background
    "card_bg": "#1A1A1A",            # Dark gray for cards
    "primary_gold": "#FFD700",        # Gold accent (main brand color)
    "secondary_gold": "#FFA500",      # Orange-gold
    "blue_accent": "#4A90E2",         # Blue accent
    "cyan_accent": "#00CED1",         # Cyan accent
    "success": "#FFD700",             # Gold for positive values
    "warning": "#FFA500",             # Orange for warnings
    "error": "#FF6B6B",               # Red for errors
    "text_primary": "#FFFFFF",        # White text
    "text_muted": "#888888",          # Gray muted text
    "border": "#333333"               # Dark borders
}

# Enhanced CSS for LuxQuant theme
st.markdown("""
<style>
.stApp { 
    background-color: #000000; 
    color: #FFFFFF;
}

/* Main metric containers */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
    border: 1px solid #333333;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    backdrop-filter: blur(10px);
}

/* Force all metric values to gold */
[data-testid="metric-container"] div[data-testid="metric-value"] {
    color: #FFD700 !important;
    font-weight: bold !important;
    font-size: 28px !important;
}

/* Metric labels */
[data-testid="metric-container"] div[data-testid="metric-label"] {
    color: #CCCCCC !important;
    font-size: 14px !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Metric delta (change indicators) */
[data-testid="metric-container"] div[data-testid="metric-delta"] {
    color: #4A90E2 !important;
    font-size: 12px !important;
}

/* Custom metric cards */
.metric-card {
    background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
    border: 1px solid #333333;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    text-align: center;
    backdrop-filter: blur(10px);
}

.metric-card h3 {
    color: #CCCCCC;
    font-size: 16px;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-card p {
    color: #FFD700;
    font-size: 24px;
    font-weight: bold;
    margin: 10px 0;
}

/* Time range info boxes */
.time-range-info {
    background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
    border: 1px solid #4A90E2;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    color: #4A90E2;
}

/* Chart containers */
.chart-container {
    background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
    border: 1px solid #333333;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 8px 24px rgba(0,0,0,0.6);
}

/* Subheaders */
h3 {
    color: #FFD700 !important;
    border-bottom: 2px solid #333333;
    padding-bottom: 10px;
}

/* Info boxes */
.stAlert {
    background-color: #1A1A1A !important;
    border: 1px solid #333333 !important;
    color: #FFFFFF !important;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #1A1A1A;
}

/* Button styling */
.stButton button {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    color: #000000;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.stButton button:hover {
    background: linear-gradient(135deg, #FFA500 0%, #FFD700 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: #1A1A1A;
    border-bottom: 1px solid #333333;
}

.stTabs [data-baseweb="tab"] {
    color: #888888;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #FFD700;
}

.stTabs [aria-selected="true"] {
    color: #FFD700 !important;
    border-bottom: 2px solid #FFD700 !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    [data-testid="metric-container"] {
        padding: 15px;
        margin: 8px 0;
    }
    
    .metric-card {
        padding: 15px;
        margin: 8px 0;
    }
    
    .metric-card p {
        font-size: 20px;
    }
}

/* Plotly chart theme adjustments */
.js-plotly-plot .plotly .main-svg {
    background-color: transparent !important;
}

.plotly-graph-div {
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    # Import modules with better error handling
    try:
        from database.connection import get_connection_status, load_data
        from data_processing.signal_processor import process_signals
        from utils.helpers import apply_filters
        from components.sidebar import render_sidebar
    except ImportError as e:
        st.error(f"Critical Import Error: {e}")
        st.info("Please ensure all required module files are in place")
        
        # Try basic sidebar as fallback
        try:
            filters = render_basic_sidebar()
        except:
            st.error("Could not load sidebar. Using basic interface.")
            return
            
        st.stop()
    
    # Header
    render_header()
    
    # Sidebar with enhanced filters
    try:
        filters = render_sidebar()
    except (ImportError, NameError) as e:
        st.warning(f"Enhanced sidebar not available: {e}")
        filters = render_basic_sidebar()
    
    # Check connection
    conn_status = get_connection_status()
    
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
        
        # Process signals with standardization
        with st.spinner("Processing and standardizing data..."):
            processed_data = process_signals(raw_data)
        
        if processed_data is None or processed_data.empty:
            st.warning("No data after processing and standardization")
            return
        
        # Apply filters (includes pair filtering and custom date range)
        filtered_data = apply_filters(processed_data, filters)
        
        # Render enhanced dashboard (WITHOUT top performers)
        render_dashboard(filtered_data, filters)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)

def render_header():
    """Render enhanced header with real-time updates"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">LuxQuant Dashboard Performance</h1>
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

def render_dashboard(data, filters):
    """Render main dashboard - REMOVED top performers section"""
    if data is None or data.empty:
        st.warning("No data available for the selected filters")
        return
    
    # Show active time range
    render_time_range_indicator(filters)
    
    # 1. Summary Cards with fallback handling
    try:
        from components.modern_metrics import render_summary_cards
        render_summary_cards(data, filters)
    except (ImportError, NameError) as e:
        st.warning(f"Modern metrics component not available: {e}")
        render_fallback_metrics(data)
    
    st.markdown("---")
    
    render_outcome_analysis(data, filters)
    st.markdown("---")
    
    
    # 2. Win Rate Trend Analysis with fallback
    try:
        from components.modern_metrics import render_winrate_trend
        render_winrate_trend(data, filters)
    except (ImportError, NameError) as e:
        st.warning(f"Enhanced winrate component not available: {e}")
        render_basic_winrate_chart(data)
    
    st.markdown("---")
    
    # 3. Additional Analytics (Performance, Rolling, RR Analysis)
    render_additional_analytics(data, filters)

def render_time_range_indicator(filters):
    """Show active time range and filters"""
    time_range = filters.get('time_range', 'all')
    
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import get_time_range_label
            time_label = get_time_range_label(time_range)
        except ImportError:
            time_label = time_range
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="time-range-info">
                📅 <strong>Active Time Range:</strong> {time_label}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if filters.get('pair_filter'):
                pairs = filters['pair_filter'].replace(' ', '').upper()
                st.markdown(f"""
                <div class="time-range-info">
                    💱 <strong>Filtered Pairs:</strong> {pairs}
                </div>
                """, unsafe_allow_html=True)

def render_additional_analytics(data, filters):
    """Render additional analytics based on available data"""
    if data is None or data.empty:
        return
    
    # Create tabs for different analytics
    tab1, tab2, tab3 = st.tabs(["📊 Performance Metrics", "📈 Rolling Analysis", "🎯 Risk-Reward"])
    
    with tab1:
        render_performance_breakdown(data, filters)
    
    with tab2:
        render_rolling_analytics(data, filters)
    
    with tab3:
        render_rr_analytics(data, filters)

def render_performance_breakdown(data, filters):
    """Render detailed performance breakdown"""
    st.subheader("Performance Breakdown")
    
    time_range = filters.get('time_range', 'all')
    
    # Apply time range filter for metrics
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import apply_time_range_filter
            filtered_data = apply_time_range_filter(data, time_range, 'created_at')
        except ImportError:
            filtered_data = data
    else:
        filtered_data = data
    
    if filtered_data.empty:
        st.info("No data available for selected time range")
        return
    
    # Calculate detailed metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Outcome distribution
        # TP Level breakdown
        if 'final_outcome' in filtered_data.columns:
            tp_data = filtered_data[filtered_data['final_outcome'].str.startswith('tp', na=False)]
    
            if not tp_data.empty:
                tp_counts = tp_data['final_outcome'].value_counts().sort_index()
                total_tp = tp_counts.sum()
        
        # Calculate percentages
                tp_percentages = (tp_counts / total_tp * 100).round(1)
        
                fig = go.Figure(data=[go.Bar(
                    x=tp_counts.index,
                    y=tp_counts.values,
                    marker_color='#00D46A',
                    text=[f"{count}<br>({pct}%)" for count, pct in zip(tp_counts.values, tp_percentages.values)],
                    textposition='inside',
                    textfont=dict(color='white', size=12)
                )])
        
                fig.update_layout(
                    title="TP Level Distribution",
                    xaxis_title="TP Level",
                    yaxis_title="Count",
                    template="plotly_dark",
                    paper_bgcolor="#1A1D24",
                    plot_bgcolor="#1A1D24",
                    height=700,
                    font=dict(color="#FFFFFF"),
                    showlegend=False
                )
        
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
    # Top 10 Best Performing Coins (Bar Chart Miring)
        if 'pair' in filtered_data.columns and 'final_outcome' in filtered_data.columns:
        # Calculate win rate per coin
            pair_stats = []
            for pair in filtered_data['pair'].unique():
                pair_data = filtered_data[filtered_data['pair'] == pair]
                closed_pair = pair_data[pair_data['final_outcome'].notna()]
            
                if len(closed_pair) >= 3:  # Minimum 3 trades
                    tp_hits = closed_pair['final_outcome'].str.startswith('tp', na=False).sum()
                    win_rate = (tp_hits / len(closed_pair) * 100)
                    pair_stats.append({
                        'pair': pair,
                        'win_rate': win_rate,
                        'trades': len(closed_pair)
                 })
        
            if pair_stats:
                pair_df = pd.DataFrame(pair_stats)
                top_10 = pair_df.nlargest(30, 'win_rate')
            
                fig = go.Figure(data=[go.Bar(
                    y=top_10['pair'][::-1],  # Reverse for top-to-bottom
                    x=top_10['win_rate'][::-1],
                    orientation='h',
                    marker_color='#00D46A',
                    text=[f"{wr:.1f}%" for wr in top_10['win_rate'][::-1]],
                    textposition='outside',
                    textfont=dict(color='white', size=10)
                )])
            
                fig.update_layout(
                    title="Top 10 Best Performing Coins",
                    xaxis_title="Win Rate (%)",
                    yaxis_title="",
                    template="plotly_dark",
                    paper_bgcolor="#1A1D24",
                    plot_bgcolor="#1A1D24", 
                    height=700,
                    font=dict(color="#FFFFFF"),
                    margin=dict(l=80, r=20, t=40, b=40),
                    xaxis=dict(range=[0, 100])
                )
            
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for top coins analysis")
        else:
            st.info("Missing data for coins analysis")

def render_rolling_analytics(data, filters):
    """Render rolling analytics with time range support"""
    st.subheader("Rolling Analysis")
    
    try:
        from components.modern_metrics import render_rolling_winrate_chart
        render_rolling_winrate_chart(data, filters)
    except ImportError:
        st.warning("Rolling analysis component not available")
        st.info("This feature requires the modern_metrics component")

def render_rr_analytics(data, filters):
    """Render risk-reward analytics"""
    st.subheader("Risk-Reward Analysis")
    
    if 'rr_planned' not in data.columns:
        st.info("No RR data available")
        return
    
    # Apply time range filter
    time_range = filters.get('time_range', 'all')
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import apply_time_range_filter
            filtered_data = apply_time_range_filter(data, time_range, 'created_at')
        except ImportError:
            filtered_data = data
    else:
        filtered_data = data
    
    rr_data = filtered_data['rr_planned'].dropna()
    
    if rr_data.empty:
        st.info("No RR data available for selected time range")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # RR Distribution
        fig = go.Figure(data=[go.Histogram(
            x=rr_data,
            nbinsx=30,
            marker_color='#4B9BFF',
            opacity=0.7
        )])
        
        fig.add_vline(
            x=rr_data.mean(),
            line_dash="dash",
            line_color="#FDB32B",
            annotation_text=f"Mean: {rr_data.mean():.2f}"
        )
        
        fig.update_layout(
            title="RR Ratio Distribution",
            xaxis_title="RR Ratio",
            yaxis_title="Count",
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            height=300,
            font=dict(color="#FFFFFF")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # RR vs Outcome (if outcome data available)
        if 'final_outcome' in filtered_data.columns:
            rr_outcome_data = filtered_data[
                filtered_data['rr_planned'].notna() & 
                filtered_data['final_outcome'].notna() & 
                (filtered_data['final_outcome'] != 'open')
            ]
            
            if not rr_outcome_data.empty:
                fig = go.Figure()
                
                for outcome in rr_outcome_data['final_outcome'].unique():
                    outcome_data = rr_outcome_data[rr_outcome_data['final_outcome'] == outcome]
                    
                    color = '#00D46A' if outcome.startswith('tp') else '#FF4747'
                    
                    fig.add_trace(go.Scatter(
                        x=outcome_data['rr_planned'],
                        y=outcome_data['pair'],
                        mode='markers',
                        name=outcome.upper(),
                        marker=dict(color=color, size=8, opacity=0.7)
                    ))
                
                fig.update_layout(
                    title="RR vs Outcome by Pair",
                    xaxis_title="RR Ratio",
                    yaxis_title="Trading Pair",
                    template="plotly_dark",
                    paper_bgcolor="#1A1D24",
                    plot_bgcolor="#1A1D24",
                    height=300,
                    font=dict(color="#FFFFFF")
                )
                
                st.plotly_chart(fig, use_container_width=True)

def render_fallback_metrics(data):
    """Fallback metrics if modern components fail"""
    st.subheader("📊 Basic Performance Overview")
    
    # Calculate basic metrics
    metrics = calculate_basic_metrics(data)
    
    # Render basic metric cards
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

def render_basic_sidebar():
    """Basic sidebar fallback if enhanced sidebar fails"""
    st.sidebar.title("LuxQuant Pro")
    st.sidebar.markdown("**Filters**")
    
    filters = {}
    filters['date_from'] = st.sidebar.date_input("From Date", value=None)
    filters['date_to'] = st.sidebar.date_input("To Date", value=None)
    filters['pair_filter'] = st.sidebar.text_input("Pairs (comma-separated)")
    filters['time_range'] = 'custom' if filters['date_from'] or filters['date_to'] else 'all'
    filters['chart_period'] = 'Daily'
    filters['show_moving_average'] = True
    filters['auto_load'] = True
    
    return filters

def render_basic_winrate_chart(data):
    """Basic winrate chart fallback"""
    st.subheader("📈 Win Rate Trend Analysis")
    
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
    
    
def render_rolling_analytics(data, filters):
    """Render rolling analytics with basic implementation"""
    st.subheader("Rolling Analysis")
    
    if 'created_at' not in data.columns or 'final_outcome' not in data.columns:
        st.info("Not enough data for rolling analysis")
        return
    
    # Filter closed trades
    closed_data = data[data['final_outcome'].notna()].copy()
    if closed_data.empty:
        st.info("No closed trades for rolling analysis")
        return
    
    # Sort by date
    closed_data['created_at'] = pd.to_datetime(closed_data['created_at'], errors='coerce')
    closed_data = closed_data.sort_values('created_at')
    closed_data['is_winner'] = closed_data['final_outcome'].str.startswith('tp', na=False)
    
    # Calculate 30-day rolling win rate
    window = 30
    closed_data['rolling_wr'] = closed_data['is_winner'].rolling(window=window, min_periods=5).mean() * 100
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=closed_data['created_at'],
        y=closed_data['rolling_wr'],
        mode='lines',
        name=f'{window}-Trade Rolling WR',
        line=dict(color='#00CED1', width=2)
    ))
    
    fig.add_hline(y=50, line_dash="dash", line_color=COLORS['text_muted'])
    
    fig.update_layout(
        title=f"{window}-Trade Rolling Win Rate",
        xaxis_title="Date",
        yaxis_title="Rolling Win Rate (%)",
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def calculate_basic_metrics(data):
    """Calculate basic summary metrics as fallback"""
    if data is None or data.empty:
        return {
            'total_signals': 0, 'closed_trades': 0, 'open_signals': 0,
            'tp_hits': 0, 'sl_hits': 0, 'win_rate': 0,
            'completion_rate': 0, 'avg_rr': 0,
            'active_pairs': 0, 'top_pair': "N/A"
        }
    
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

def render_outcome_analysis(data, filters):
    """Render outcome distribution pie chart and target increase breakdown"""
    st.subheader("📊 Outcome Analysis")
    
    time_range = filters.get('time_range', 'all')
    
    # Apply time range filter
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import apply_time_range_filter
            filtered_data = apply_time_range_filter(data, time_range, 'created_at')
        except ImportError:
            filtered_data = data
    else:
        filtered_data = data
    
    if filtered_data.empty:
        st.info("No data available for selected time range")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Outcome Distribution Pie Chart (exclude 'open')
        if 'final_outcome' in filtered_data.columns:
            # Filter out 'open' outcomes for pie chart
            closed_data = filtered_data[filtered_data['final_outcome'].notna() & (filtered_data['final_outcome'] != 'open')]
            
            if not closed_data.empty:
                outcome_counts = closed_data['final_outcome'].value_counts()
                
                fig = go.Figure(data=[go.Pie(
                    labels=outcome_counts.index,
                    values=outcome_counts.values,
                    hole=0.4,
                    marker=dict(colors=['#FFD700', '#4A90E2', '#FFA500', 
                                      '#00CED1', '#FF6B6B']),
                    textinfo='label+percent+value',
                    textposition='outside'
                )])
                
                fig.update_layout(
                    title="Closed Trades Distribution",
                    template="plotly_dark",
                    paper_bgcolor="#1A1A1A",
                    plot_bgcolor="#1A1A1A",
                    height=400,
                    font=dict(color="#FFFFFF")
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No closed trades data available")
        else:
            st.info("No outcome data available")
    
    with col2:
        # Average Increase per Target Level (improved layout)
        st.markdown("**🎯 Average Increase per Target Level**")
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        
        if all(col in filtered_data.columns for col in ['entry', 'target1', 'target2', 'target3', 'target4']):
            # Create 2 rows of 2 columns for better balance
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            
            # Calculate and display metrics for each target
            for i in range(1, 5):
                target_col = f'target{i}'
                
                # Get data where both entry and target exist
                valid_data = filtered_data[
                    filtered_data['entry'].notna() & 
                    filtered_data[target_col].notna()
                ]
                
                # Select the appropriate column based on position
                if i == 1:
                    current_col = row1_col1
                elif i == 2:
                    current_col = row1_col2
                elif i == 3:
                    current_col = row2_col1
                else:  # i == 4
                    current_col = row2_col2
                
                with current_col:
                    if not valid_data.empty:
                        # Calculate percentage increase
                        increases = ((valid_data[target_col] - valid_data['entry']) / valid_data['entry'] * 100)
                        avg_increase = increases.mean()
                        
                        # Custom styled metric card
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; margin-bottom: 15px;">
                            <h3 style="color: #FFFFFF; margin: 0; font-size: 18px;">TP{i}</h3>
                            <p style="color: #00D46A; font-size: 24px; font-weight: bold; margin: 10px 0;">
                                +{avg_increase:.2f}%
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; margin-bottom: 15px;">
                            <h3 style="color: #FFFFFF; margin: 0; font-size: 18px;">TP{i}</h3>
                            <p style="color: #6B6B6B; font-size: 24px; font-weight: bold; margin: 10px 0;">
                                No data
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Missing entry/target columns for analysis")

if __name__ == "__main__":
    main()
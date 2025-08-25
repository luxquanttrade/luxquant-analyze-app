"""
LuxQuant Pro - Enhanced Version
Professional Trading Signals Analytics Dashboard with Time Range Support
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

# Enhanced CSS for dark theme with responsive design
st.markdown("""
<style>
.stApp { 
    background-color: #0E1117; 
}

[data-testid="metric-container"] {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.metric-card {
    background: linear-gradient(135deg, #1A1D24 0%, #252831 100%);
    border: 1px solid #2D3139;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    text-align: center;
}

.time-range-info {
    background-color: rgba(75, 155, 255, 0.1);
    border: 1px solid #4B9BFF;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
}

.chart-container {
    background-color: #1A1D24;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}

/* Responsive chart fixes */
.js-plotly-plot .plotly .main-svg {
    width: 100% !important;
    height: auto !important;
}

.js-plotly-plot .plotly .svg-container {
    width: 100% !important;
    height: 400px !important;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
    .js-plotly-plot .plotly .main-svg {
        height: 350px !important;
    }
    
    [data-testid="metric-container"] {
        padding: 10px;
        margin: 5px 0;
    }
    
    .metric-card {
        padding: 15px;
        margin: 5px 0;
    }
}

/* Fix for plotly responsiveness */
.plotly-graph-div {
    width: 100% !important;
}

.plotly .main-svg {
    overflow: visible !important;
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
        
        # Render enhanced dashboard
        render_dashboard(filtered_data, filters)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)

def render_header():
    """Render enhanced header with real-time updates"""
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

def render_dashboard(data, filters):
    """Render enhanced main dashboard with time range support"""
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
    
    # 2. Win Rate Trend Analysis with fallback
    try:
        from components.modern_metrics import render_winrate_trend
        render_winrate_trend(data, filters)
    except (ImportError, NameError) as e:
        st.warning(f"Enhanced winrate component not available: {e}")
        render_basic_winrate_chart(data)
    
    st.markdown("---")
    
    # 3. Top Performers with fallback
    try:
        from components.top_performers import render_top_performers
        render_top_performers(data)
    except (ImportError, NameError) as e:
        st.warning(f"Top performers component not available: {e}")
        render_basic_top_performers(data)
    
    st.markdown("---")


def render_time_range_indicator(filters):
    """Show active time range and filters"""
    time_range = filters.get('time_range', 'all')
    
    if time_range != 'all':
        from data_processing.winrate_calculator import get_time_range_label
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="time-range-info">
                📅 <strong>Active Time Range:</strong> {get_time_range_label(time_range)}
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
        from data_processing.winrate_calculator import apply_time_range_filter
        filtered_data = apply_time_range_filter(data, time_range, 'created_at')
    else:
        filtered_data = data
    
    if filtered_data.empty:
        st.info("No data available for selected time range")
        return
    
    # Calculate detailed metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Outcome distribution
        if 'final_outcome' in filtered_data.columns:
            outcome_counts = filtered_data['final_outcome'].fillna('open').value_counts()
            
            fig = go.Figure(data=[go.Pie(
                labels=outcome_counts.index,
                values=outcome_counts.values,
                hole=0.4,
                marker=dict(colors=['#00D46A', '#FF4747', '#FDB32B', '#4B9BFF', '#9D5CFF'])
            )])
            
            fig.update_layout(
                title="Outcome Distribution",
                template="plotly_dark",
                paper_bgcolor="#1A1D24",
                plot_bgcolor="#1A1D24",
                height=300,
                font=dict(color="#FFFFFF")
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # TP Level breakdown
        if 'final_outcome' in filtered_data.columns:
            tp_data = filtered_data[filtered_data['final_outcome'].str.startswith('tp', na=False)]
            
            if not tp_data.empty:
                tp_counts = tp_data['final_outcome'].value_counts().sort_index()
                
                fig = go.Figure(data=[go.Bar(
                    x=tp_counts.index,
                    y=tp_counts.values,
                    marker_color='#00D46A'
                )])
                
                fig.update_layout(
                    title="TP Level Distribution",
                    xaxis_title="TP Level",
                    yaxis_title="Count",
                    template="plotly_dark",
                    paper_bgcolor="#1A1D24",
                    plot_bgcolor="#1A1D24",
                    height=300,
                    font=dict(color="#FFFFFF")
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No TP data available")

def render_rolling_analytics(data, filters):
    """Render rolling analytics with time range support"""
    st.subheader("Rolling Analysis")
    
    try:
        from components.modern_metrics import render_rolling_winrate_chart
        render_rolling_winrate_chart(data, filters)
    except ImportError:
        st.warning("Rolling analysis component not available")

def render_rr_analytics(data, filters):
    """Render risk-reward analytics"""
    st.subheader("Risk-Reward Analysis")
    
    if 'rr_planned' not in data.columns:
        st.info("No RR data available")
        return
    
    # Apply time range filter
    time_range = filters.get('time_range', 'all')
    if time_range != 'all':
        from data_processing.winrate_calculator import apply_time_range_filter
        filtered_data = apply_time_range_filter(data, time_range, 'created_at')
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
            nbins=30,
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

def render_basic_top_performers(data):
    """Basic top performers fallback"""
    st.subheader("🏆 Top Performers")
    
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
    """Calculate basic summary metrics as fallback"""
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
    
def calculate_basic_metrics(data):
    """Calculate basic summary metrics as fallback"""
    metrics = {}
    
    if data is None or data.empty:
        return {
            'total_signals': 0, 'closed_trades': 0, 'open_signals': 0,
            'tp_hits': 0, 'sl_hits': 0, 'win_rate': 0,
            'completion_rate': 0, 'avg_rr': 0,
            'active_pairs': 0, 'top_pair': "N/A"
        }
    
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

if __name__ == "__main__":
    main()
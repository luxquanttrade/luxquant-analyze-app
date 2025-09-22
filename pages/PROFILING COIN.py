"""
🪙 Coin Profiling - LuxQuant Pro
Individual coin performance analysis with detailed metrics
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="🪙 Coin Profiling - LuxQuant Pro",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modules with error handling
try:
    from database.connection import get_connection_status, load_data
    from data_processing.signal_processor import process_signals
    from utils.helpers import apply_filters, format_number
    from config.theme import COLORS, CUSTOM_CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
except ImportError as e:
    st.error(f"Import Error: {e}")
    # Fallback colors
    COLORS = {
        "green": "#00D46A",
        "red": "#FF4747",
        "blue": "#4B9BFF",
        "background": "#0E1117"
    }

def render_page_header():
    """Render page header"""
    st.markdown("""
    <div style="margin-bottom: 30px;">
        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">
            🪙 Coin Profiling
        </h1>
        <p style="color: #A0A0A0; font-size: 16px; margin-top: 10px;">
            Individual coin performance analysis with detailed metrics and insights
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_coin_selector(data):
    """Render coin selection dropdown"""
    st.sidebar.title("🪙 Coin Selection")
    
    if data is None or data.empty or 'pair' not in data.columns:
        st.sidebar.error("No coin data available")
        return None
    
    # Get unique pairs
    available_coins = sorted(data['pair'].dropna().unique())
    
    if not available_coins:
        st.sidebar.warning("No coins found in data")
        return None
    
    selected_coin = st.sidebar.selectbox(
        "Select Coin to Analyze",
        available_coins,
        help="Choose a trading pair for detailed analysis"
    )
    
    # Show coin info
    coin_signals = len(data[data['pair'] == selected_coin])
    st.sidebar.info(f"📊 **{selected_coin}**\n\n• Total Signals: {coin_signals:,}")
    
    return selected_coin

def calculate_coin_metrics(data, coin):
    """Calculate comprehensive metrics for selected coin"""
    coin_data = data[data['pair'] == coin].copy()
    
    metrics = {
        'coin': coin,
        'total_signals': len(coin_data),
        'closed_trades': 0,
        'open_signals': 0,
        'overall_wr': 0,
        'tp1_count': 0,
        'tp2_count': 0, 
        'tp3_count': 0,
        'tp4_count': 0,
        'sl_count': 0,
        'tp1_rate': 0,
        'tp2_rate': 0,
        'tp3_rate': 0, 
        'tp4_rate': 0,
        'sl_rate': 0,
        'avg_rr': 0,
        'best_rr': 0,
        'worst_rr': 0,
        'median_rr': 0
    }
    
    # Calculate closed trades
    if 'final_outcome' in coin_data.columns:
        closed_data = coin_data[coin_data['final_outcome'].notna() & (coin_data['final_outcome'] != 'open')]
        metrics['closed_trades'] = len(closed_data)
        metrics['open_signals'] = metrics['total_signals'] - metrics['closed_trades']
        
        if metrics['closed_trades'] > 0:
            # TP level counts
            metrics['tp1_count'] = (closed_data['final_outcome'] == 'tp1').sum()
            metrics['tp2_count'] = (closed_data['final_outcome'] == 'tp2').sum()
            metrics['tp3_count'] = (closed_data['final_outcome'] == 'tp3').sum()
            metrics['tp4_count'] = (closed_data['final_outcome'] == 'tp4').sum()
            metrics['sl_count'] = (closed_data['final_outcome'] == 'sl').sum()
            
            # Calculate rates
            total_closed = metrics['closed_trades']
            metrics['tp1_rate'] = (metrics['tp1_count'] / total_closed * 100)
            metrics['tp2_rate'] = (metrics['tp2_count'] / total_closed * 100)
            metrics['tp3_rate'] = (metrics['tp3_count'] / total_closed * 100)
            metrics['tp4_rate'] = (metrics['tp4_count'] / total_closed * 100)
            metrics['sl_rate'] = (metrics['sl_count'] / total_closed * 100)
            
            # Overall win rate
            total_tp = metrics['tp1_count'] + metrics['tp2_count'] + metrics['tp3_count'] + metrics['tp4_count']
            metrics['overall_wr'] = (total_tp / total_closed * 100)
    else:
        metrics['open_signals'] = metrics['total_signals']
    
    # RR metrics
    if 'rr_planned' in coin_data.columns:
        rr_data = coin_data['rr_planned'].dropna()
        if len(rr_data) > 0:
            metrics['avg_rr'] = rr_data.mean()
            metrics['best_rr'] = rr_data.max()
            metrics['worst_rr'] = rr_data.min()
            metrics['median_rr'] = rr_data.median()
    
    return metrics

def render_coin_overview(metrics):
    """Render coin overview cards"""
    st.markdown(f"## 🪙 {metrics['coin']} Performance Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📊 Total Signals", 
            f"{metrics['total_signals']:,}",
            help="Total number of signals for this coin"
        )
    
    with col2:
        wr_color = "normal" if metrics['overall_wr'] >= 50 else "inverse"
        st.metric(
            "🏆 Overall Win Rate", 
            f"{metrics['overall_wr']:.1f}%",
            delta=f"{'Above' if metrics['overall_wr'] >= 50 else 'Below'} 50%",
            delta_color=wr_color,
            help="Percentage of winning trades (TP hits)"
        )
    
    with col3:
        st.metric(
            "✅ Closed Trades", 
            f"{metrics['closed_trades']:,}",
            help="Number of completed trades with outcomes"
        )
    
    with col4:
        st.metric(
            "🔄 Open Signals", 
            f"{metrics['open_signals']:,}",
            help="Number of active/pending signals"
        )
    
    with col5:
        rr_color = "normal" if metrics['avg_rr'] >= 2 else "inverse"
        st.metric(
            "⚖️ Avg RR Ratio", 
            f"{metrics['avg_rr']:.2f}",
            delta=f"{'Good' if metrics['avg_rr'] >= 2 else 'Low'} RR",
            delta_color=rr_color,
            help="Average risk-reward ratio"
        )

def render_tp_level_breakdown(metrics):
    """Render TP level breakdown chart"""
    st.markdown("### 🎯 Take Profit Level Performance")
    
    if metrics['closed_trades'] == 0:
        st.info("No closed trades available for TP analysis")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # TP breakdown pie chart
        labels = ['TP1', 'TP2', 'TP3', 'TP4', 'SL']
        values = [
            metrics['tp1_count'],
            metrics['tp2_count'], 
            metrics['tp3_count'],
            metrics['tp4_count'],
            metrics['sl_count']
        ]
        
        colors = [COLORS['green'], COLORS['blue'], COLORS['yellow'], COLORS['purple'], COLORS['red']]
        
        # Filter out zero values
        filtered_data = [(label, value, color) for label, value, color in zip(labels, values, colors) if value > 0]
        
        if not filtered_data:
            st.info("No outcome data available")
            return
        
        labels_filtered, values_filtered, colors_filtered = zip(*filtered_data)
        
        fig = go.Figure(data=[go.Pie(
            labels=labels_filtered,
            values=values_filtered,
            hole=0.4,
            marker=dict(colors=colors_filtered),
            textinfo='label+percent+value',
            textposition='outside'
        )])
        
        fig.update_layout(
            title=f"{metrics['coin']} - Outcome Distribution",
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            font=dict(color="#FFFFFF"),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # TP rates metrics
        st.markdown("**📈 Hit Rates:**")
        
        if metrics['tp1_count'] > 0:
            st.metric("🥇 TP1 Rate", f"{metrics['tp1_rate']:.1f}%", 
                     f"{metrics['tp1_count']} hits")
        
        if metrics['tp2_count'] > 0:
            st.metric("🥈 TP2 Rate", f"{metrics['tp2_rate']:.1f}%", 
                     f"{metrics['tp2_count']} hits")
        
        if metrics['tp3_count'] > 0:
            st.metric("🥉 TP3 Rate", f"{metrics['tp3_rate']:.1f}%", 
                     f"{metrics['tp3_count']} hits")
        
        if metrics['tp4_count'] > 0:
            st.metric("🏆 TP4 Rate", f"{metrics['tp4_rate']:.1f}%", 
                     f"{metrics['tp4_count']} hits")
        
        if metrics['sl_count'] > 0:
            st.metric("🔴 SL Rate", f"{metrics['sl_rate']:.1f}%", 
                     f"{metrics['sl_count']} hits", delta_color="inverse")

def render_performance_timeline(data, coin):
    """Render performance over time"""
    st.markdown("### 📈 Performance Timeline")
    
    coin_data = data[data['pair'] == coin].copy()
    
    if 'created_at' not in coin_data.columns:
        st.info("No timeline data available")
        return
    
    # Filter closed trades only
    closed_data = coin_data[coin_data['final_outcome'].notna() & (coin_data['final_outcome'] != 'open')].copy()
    
    if closed_data.empty:
        st.info("No closed trades for timeline analysis")
        return
    
    # Ensure datetime format
    closed_data['created_at'] = pd.to_datetime(closed_data['created_at'], errors='coerce')
    closed_data = closed_data[closed_data['created_at'].notna()]
    
    if closed_data.empty:
        st.info("No valid date data for timeline")
        return
    
    # Create daily aggregation
    closed_data['date'] = closed_data['created_at'].dt.date
    closed_data['is_winner'] = closed_data['final_outcome'].str.startswith('tp', na=False)
    
    daily_stats = closed_data.groupby('date').agg({
        'is_winner': ['sum', 'count']
    }).reset_index()
    
    daily_stats.columns = ['date', 'wins', 'total']
    daily_stats['win_rate'] = (daily_stats['wins'] / daily_stats['total'] * 100)
    daily_stats['cumulative_wr'] = (daily_stats['wins'].cumsum() / daily_stats['total'].cumsum() * 100)
    
    # Timeline chart
    fig = go.Figure()
    
    # Daily win rate
    fig.add_trace(go.Scatter(
        x=daily_stats['date'],
        y=daily_stats['win_rate'],
        mode='lines+markers',
        name='Daily Win Rate',
        line=dict(color=COLORS['blue'], width=2),
        marker=dict(size=6)
    ))
    
    # Cumulative win rate
    fig.add_trace(go.Scatter(
        x=daily_stats['date'],
        y=daily_stats['cumulative_wr'],
        mode='lines',
        name='Cumulative Win Rate',
        line=dict(color=COLORS['green'], width=3),
    ))
    
    # 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color=COLORS['text_muted'], opacity=0.7)
    
    fig.update_layout(
        title=f"{coin} - Win Rate Timeline",
        xaxis_title="Date",
        yaxis_title="Win Rate (%)",
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#1A1D24",
        font=dict(color="#FFFFFF"),
        hovermode='x unified',
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Latest Daily WR", f"{daily_stats['win_rate'].iloc[-1]:.1f}%")
    with col2:
        st.metric("Cumulative WR", f"{daily_stats['cumulative_wr'].iloc[-1]:.1f}%")
    with col3:
        st.metric("Trading Days", f"{len(daily_stats)}")

def render_rr_analysis(data, coin, metrics):
    """Render RR analysis for the coin"""
    st.markdown("### ⚖️ Risk-Reward Analysis")
    
    coin_data = data[data['pair'] == coin].copy()
    
    if 'rr_planned' not in coin_data.columns:
        st.info("No RR data available for analysis")
        return
    
    rr_data = coin_data['rr_planned'].dropna()
    
    if rr_data.empty:
        st.info(f"No RR data available for {coin}")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**📊 RR Statistics:**")
        st.metric("📈 Average RR", f"{metrics['avg_rr']:.2f}")
        st.metric("🚀 Best RR", f"{metrics['best_rr']:.2f}")
        st.metric("📉 Worst RR", f"{metrics['worst_rr']:.2f}")
        st.metric("📊 Median RR", f"{metrics['median_rr']:.2f}")
        
        # RR quality assessment
        if metrics['avg_rr'] >= 3:
            st.success("🔥 Excellent RR Profile")
        elif metrics['avg_rr'] >= 2:
            st.info("👍 Good RR Profile")
        else:
            st.warning("⚠️ Low RR Profile")
    
    with col2:
        # RR distribution chart
        fig = go.Figure(data=[go.Histogram(
            x=rr_data,
            nbinsx=min(20, len(rr_data)//2),
            marker=dict(color=COLORS['blue'], opacity=0.7),
            name="RR Distribution"
        )])
        
        # Add mean line
        fig.add_vline(
            x=metrics['avg_rr'],
            line_dash="dash",
            line_color=COLORS['yellow'],
            annotation_text=f"Mean: {metrics['avg_rr']:.2f}",
            annotation_position="top"
        )
        
        fig.update_layout(
            title=f"{coin} - RR Ratio Distribution",
            xaxis_title="RR Ratio",
            yaxis_title="Count",
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            font=dict(color="#FFFFFF"),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # RR vs Outcome Analysis
    if 'final_outcome' in coin_data.columns:
        st.markdown("#### 🎯 RR Performance by Outcome")
        
        rr_outcome_data = coin_data[
            coin_data['rr_planned'].notna() & 
            coin_data['final_outcome'].notna() &
            (coin_data['final_outcome'] != 'open')
        ]
        
        if not rr_outcome_data.empty:
            fig = px.box(
                rr_outcome_data,
                x='final_outcome',
                y='rr_planned',
                title=f"{coin} - RR by Outcome",
                color='final_outcome',
                color_discrete_map={
                    'tp1': COLORS['green'],
                    'tp2': COLORS['blue'],
                    'tp3': COLORS['yellow'],
                    'tp4': COLORS['purple'],
                    'sl': COLORS['red']
                }
            )
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1A1D24",
                plot_bgcolor="#1A1D24",
                font=dict(color="#FFFFFF"),
                xaxis_title="Outcome",
                yaxis_title="Planned RR Ratio"
            )
            
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main function"""
    # Render header
    render_page_header()
    
    # Check database connection
    conn_status = get_connection_status()
    if not conn_status.get("connected"):
        st.error("❌ Database connection failed")
        st.code(conn_status.get('error', 'Unknown error'))
        return
    
    # Load and process data
    try:
        with st.spinner("🔄 Loading signal data..."):
            raw_data = load_data()
        
        if not raw_data or 'signals' not in raw_data:
            st.error("❌ No signal data found")
            return
        
        with st.spinner("🔧 Processing data..."):
            processed_data = process_signals(raw_data)
        
        if processed_data is None or processed_data.empty:
            st.warning("⚠️ No data after processing")
            return
        
        # Render coin selector
        selected_coin = render_coin_selector(processed_data)
        
        if not selected_coin:
            st.info("👆 Please select a coin from the sidebar to analyze")
            return
        
        # Calculate metrics for selected coin
        with st.spinner(f"📊 Analyzing {selected_coin}..."):
            metrics = calculate_coin_metrics(processed_data, selected_coin)
        
        # Render analysis sections
        render_coin_overview(metrics)
        st.markdown("---")
        
        render_tp_level_breakdown(metrics)
        st.markdown("---")
        
        render_performance_timeline(processed_data, selected_coin)
        st.markdown("---")
        
        render_rr_analysis(processed_data, selected_coin, metrics)
        
        # Additional insights
        with st.expander("💡 Analysis Insights"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 Performance Insights:**")
                if metrics['overall_wr'] >= 60:
                    st.success(f"🔥 {selected_coin} shows excellent performance with {metrics['overall_wr']:.1f}% win rate!")
                elif metrics['overall_wr'] >= 50:
                    st.info(f"👍 {selected_coin} has decent performance with {metrics['overall_wr']:.1f}% win rate.")
                else:
                    st.warning(f"⚠️ {selected_coin} underperforming with {metrics['overall_wr']:.1f}% win rate.")
            
            with col2:
                st.markdown("**⚖️ Risk-Reward Insights:**")
                if metrics['avg_rr'] >= 3:
                    st.success(f"🚀 Excellent RR profile at {metrics['avg_rr']:.2f} - great risk management!")
                elif metrics['avg_rr'] >= 2:
                    st.info(f"📈 Good RR profile at {metrics['avg_rr']:.2f} - solid strategy.")
                else:
                    st.warning(f"📉 Low RR profile at {metrics['avg_rr']:.2f} - consider better targets.")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
"""
Winrate display components
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_processing.winrate_calculator import (
    calculate_period_winrates, 
    calculate_winrate_trend,
    get_winrate_summary_stats,
    calculate_rolling_winrate
)

def render_winrate_section(data):
    """Main winrate analysis section"""
    if data is None or data.empty:
        st.warning("No data available for winrate analysis")
        return
        
    st.subheader("Winrate Trend Analysis")
    
    # Period filter
    col1, col2 = st.columns([1, 3])
    
    with col1:
        period_filter = st.selectbox(
            "Analysis Period",
            ["All Time (Monthly)", "Recent Months (Daily)"],
            help="All Time shows monthly breakdown, Recent Months shows daily breakdown"
        )
    
    # Convert to period codes
    period_code = 'A' if period_filter.startswith("All Time") else 'M'
    
    # Calculate winrate data
    winrate_data = calculate_period_winrates(data, period=period_code)
    
    if winrate_data.empty:
        st.info("No closed trades found for winrate analysis")
        return
    
    # Display main chart and stats
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_winrate_trendline_chart(winrate_data, period_filter)
    
    with col2:
        render_winrate_stats(data, winrate_data)
    
    # Additional analysis
    render_rolling_winrate(data)

def render_winrate_trendline_chart(winrate_data, period_name):
    """Render winrate trendline chart"""
    fig = go.Figure()
    
    # Main winrate line
    fig.add_trace(go.Scatter(
        x=winrate_data['period_date'],
        y=winrate_data['winrate'],
        mode='lines+markers',
        name='Win Rate',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8),
        hovertemplate='Period: %{x}<br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>',
        customdata=winrate_data['total_trades']
    ))
    
    # Add trendline
    if len(winrate_data) >= 2:
        trend_info = calculate_winrate_trend(winrate_data)
        
        # Simple linear trendline
        x_numeric = list(range(len(winrate_data)))
        z = pd.Series(winrate_data['winrate']).interpolate()
        trendline = z.rolling(window=min(3, len(z)), center=True).mean()
        
        fig.add_trace(go.Scatter(
            x=winrate_data['period_date'],
            y=trendline,
            mode='lines',
            name='Trend',
            line=dict(color='#F18F01', width=2, dash='dot'),
            opacity=0.7
        ))
    
    # Add 50% reference line
    fig.add_hline(
        y=50, 
        line_dash="dash", 
        line_color="gray", 
        opacity=0.5,
        annotation_text="Break Even (50%)"
    )
    
    fig.update_layout(
        title=f"Win Rate Trend - {period_name}",
        xaxis_title="Time Period",
        yaxis_title="Win Rate (%)",
        yaxis=dict(range=[0, 100]),
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_winrate_stats(data, winrate_data):
    """Render winrate statistics"""
    stats = get_winrate_summary_stats(data)
    
    if 'error' in stats:
        st.error(stats['error'])
        return
    
    st.markdown("**Overall Statistics**")
    
    # Main metrics
    st.metric("Overall Win Rate", f"{stats['overall_winrate']:.1f}%")
    st.metric("Total Trades", f"{stats['total_trades']:,}")
    
    st.markdown("---")
    st.markdown("**Outcome Breakdown**")
    
    # TP breakdown
    tp_data = {
        'TP1': stats['tp1_count'],
        'TP2': stats['tp2_count'], 
        'TP3': stats['tp3_count'],
        'TP4': stats['tp4_count'],
        'SL': stats['sl_count']
    }
    
    for outcome, count in tp_data.items():
        if count > 0:
            percentage = (count / stats['total_trades'] * 100)
            st.write(f"• {outcome}: {count} ({percentage:.1f}%)")
    
    # Trend analysis
    if not winrate_data.empty:
        trend_info = calculate_winrate_trend(winrate_data)
        
        st.markdown("---")
        st.markdown("**Trend Analysis**")
        
        trend_colors = {
            'improving': '🟢',
            'declining': '🔴', 
            'stable': '🟡',
            'insufficient_data': '⚪'
        }
        
        trend_icon = trend_colors.get(trend_info['trend'], '⚪')
        st.write(f"{trend_icon} **{trend_info['trend'].title()}**")
        
        if trend_info['trend'] != 'insufficient_data':
            st.write(f"Slope: {trend_info['slope']:.3f}%/period")
            st.write(f"Recent: {trend_info['current_winrate']:.1f}%")

def render_rolling_winrate(data):
    """Render rolling winrate chart"""
    st.subheader("Rolling Win Rate (30-Trade Window)")
    
    rolling_data = calculate_rolling_winrate(data, window=30)
    
    if rolling_data.empty:
        st.info("Insufficient data for rolling winrate")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=rolling_data['created_at'],
        y=rolling_data['rolling_winrate'],
        mode='lines',
        name='30-Trade Rolling Win Rate',
        line=dict(color='#A23B72', width=2),
        fill='tonexty',
        fillcolor='rgba(162, 59, 114, 0.1)'
    ))
    
    # Add 50% reference line
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="Break Even"
    )
    
    fig.update_layout(
        title="Rolling Win Rate Over Time",
        xaxis_title="Date",
        yaxis_title="Win Rate (%)",
        yaxis=dict(range=[0, 100]),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show recent performance
    if len(rolling_data) > 0:
        recent_winrate = rolling_data['rolling_winrate'].iloc[-1]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Rolling WR", f"{recent_winrate:.1f}%")
        with col2:
            avg_rolling = rolling_data['rolling_winrate'].mean()
            st.metric("Average Rolling WR", f"{avg_rolling:.1f}%")
        with col3:
            max_rolling = rolling_data['rolling_winrate'].max()
            st.metric("Peak Rolling WR", f"{max_rolling:.1f}%")

def render_winrate_heatmap(data):
    """Render winrate heatmap by day/hour"""
    if data is None or data.empty or 'created_at' not in data.columns:
        return
    
    closed_df = data[data['final_outcome'].notna() & (data['final_outcome'] != 'open')].copy()
    
    if closed_df.empty:
        return
    
    st.subheader("Win Rate Heatmap by Time")
    
    # Extract hour and day of week
    closed_df['hour'] = closed_df['created_at'].dt.hour
    closed_df['day_of_week'] = closed_df['created_at'].dt.day_name()
    closed_df['is_winner'] = closed_df['final_outcome'].str.startswith('tp', na=False)
    
    # Calculate winrate by hour and day
    heatmap_data = closed_df.groupby(['day_of_week', 'hour']).agg({
        'is_winner': ['sum', 'count']
    }).reset_index()
    
    heatmap_data.columns = ['day_of_week', 'hour', 'wins', 'total']
    heatmap_data['winrate'] = (heatmap_data['wins'] / heatmap_data['total'] * 100).round(1)
    
    # Create pivot table for heatmap
    heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='winrate')
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_pivot.reindex(day_order)
    
    # Create heatmap
    fig = px.imshow(
        heatmap_pivot,
        labels=dict(x="Hour of Day", y="Day of Week", color="Win Rate %"),
        color_continuous_scale="RdYlGn",
        aspect="auto"
    )
    
    fig.update_layout(
        title="Win Rate by Day of Week and Hour",
        xaxis_title="Hour of Day (UTC)",
        yaxis_title="Day of Week"
    )
    
    st.plotly_chart(fig, use_container_width=True)
"""
Chart components for LuxQuant Analyzer
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config.settings import CHART_COLORS, DISPLAY_SETTINGS
from data_processing.metrics_calculator import calculate_pair_metrics, get_rr_distribution

def render_all_charts(data):
    """Render all chart components"""
    if data is None or data.empty:
        st.warning("No data available for charts")
        return
    
    st.markdown("---")
    
    # Main charts row
    render_outcome_and_stats(data)
    
    # Pair performance charts
    render_pair_performance_charts(data)
    
    # Risk-reward analysis charts
    render_rr_analysis_charts(data)
    
    # Timeline analysis
    render_timeline_charts(data)

def render_outcome_and_stats(data):
    """Render outcome distribution and quick stats"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_outcome_distribution(data)
    
    with col2:
        render_quick_stats_box(data)

def render_outcome_distribution(data):
    """Render outcome distribution pie chart"""
    st.subheader("Outcome Distribution")
    
    if 'final_outcome' not in data.columns:
        st.info("No outcome data available")
        return
    
    # Get outcome counts
    outcome_counts = data['final_outcome'].fillna('open').value_counts()
    
    if outcome_counts.empty:
        st.info("No outcome data to display")
        return
    
    # Create pie chart
    fig = px.pie(
        values=outcome_counts.values,
        names=outcome_counts.index,
        title="Signal Outcomes Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_quick_stats_box(data):
    """Render quick stats in a box format"""
    st.subheader("Quick Stats")
    
    # Calculate basic stats
    stats_data = []
    
    if 'pair' in data.columns:
        stats_data.append(f"**Total Pairs:** {data['pair'].nunique()}")
    
    if 'created_at' in data.columns and data['created_at'].notna().any():
        date_min = data['created_at'].min().date()
        date_max = data['created_at'].max().date()
        stats_data.append(f"**Date Range:** {date_min} to {date_max}")
    
    if 'is_open' in data.columns:
        open_signals = data['is_open'].sum()
        stats_data.append(f"**Open Signals:** {open_signals:,}")
    
    if 'rr_planned' in data.columns:
        rr_data = data['rr_planned'].dropna()
        if len(rr_data) > 0:
            stats_data.append(f"**RR Range:** {rr_data.min():.1f} - {rr_data.max():.1f}")
    
    # Display stats
    for stat in stats_data:
        st.write(stat)
    
    # Additional metrics
    if 'final_outcome' in data.columns:
        closed_trades = (~data['final_outcome'].isna()).sum()
        st.write(f"**Closed Trades:** {closed_trades:,}")

def render_pair_performance_charts(data):
    """Render pair performance charts"""
    if 'pair' not in data.columns or data['pair'].nunique() <= 1:
        return
    
    st.subheader("Performance by Trading Pair")
    
    # Calculate pair metrics
    pair_metrics = calculate_pair_metrics(data)
    
    if pair_metrics.empty:
        st.info("No pair performance data available")
        return
    
    # Filter pairs with minimum signals
    min_signals = DISPLAY_SETTINGS['min_pair_signals']
    filtered_pairs = pair_metrics[pair_metrics['total_signals'] >= min_signals].copy()
    
    if filtered_pairs.empty:
        st.info(f"No pairs with minimum {min_signals} signals found")
        return
    
    # Display pair performance table
    render_pair_performance_table(filtered_pairs)
    
    # Win rate chart
    render_win_rate_chart(filtered_pairs)

def render_pair_performance_table(pair_metrics):
    """Render pair performance table"""
    display_df = pair_metrics.copy()
    
    # Select relevant columns
    cols = ['pair', 'total_signals', 'tp_hits', 'sl_hits', 'win_rate', 'avg_rr_planned']
    available_cols = [col for col in cols if col in display_df.columns]
    display_df = display_df[available_cols]
    
    # Format columns
    if 'win_rate' in display_df.columns:
        display_df['win_rate'] = display_df['win_rate'].round(1)
    if 'avg_rr_planned' in display_df.columns:
        display_df['avg_rr_planned'] = display_df['avg_rr_planned'].round(2)
    
    st.dataframe(display_df, use_container_width=True)

def render_win_rate_chart(pair_metrics):
    """Render win rate by pair chart"""
    if 'win_rate' not in pair_metrics.columns:
        return
    
    # Get top pairs for chart
    top_limit = DISPLAY_SETTINGS['top_pairs_limit']
    top_pairs = pair_metrics.head(top_limit)
    
    if top_pairs.empty:
        return
    
    fig = px.bar(
        top_pairs,
        x='pair',
        y='win_rate',
        title=f"Win Rate by Pair (Top {len(top_pairs)})",
        color='win_rate',
        color_continuous_scale='viridis',
        labels={'win_rate': 'Win Rate (%)', 'pair': 'Trading Pair'}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis=dict(range=[0, 100]),
        showlegend=False
    )
    
    fig.update_traces(
        hovertemplate='%{x}<br>Win Rate: %{y:.1f}%<br>Total Signals: %{customdata}<extra></extra>',
        customdata=top_pairs['total_signals']
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_rr_analysis_charts(data):
    """Render risk-reward analysis charts"""
    if 'rr_planned' not in data.columns:
        return
    
    st.subheader("Risk-Reward Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_rr_distribution_chart(data)
    
    with col2:
        render_rr_vs_outcome_chart(data)

def render_rr_distribution_chart(data):
    """Render RR distribution histogram"""
    rr_data = data['rr_planned'].dropna()
    
    if len(rr_data) == 0:
        st.info("No RR data available for distribution")
        return
    
    fig = px.histogram(
        x=rr_data,
        nbins=30,
        title="Risk-Reward Ratio Distribution",
        labels={'x': 'RR Ratio', 'count': 'Number of Signals'}
    )
    
    fig.update_layout(
        xaxis_title="RR Ratio",
        yaxis_title="Count",
        bargap=0.1
    )
    
    # Add mean line
    mean_rr = rr_data.mean()
    fig.add_vline(
        x=mean_rr,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_rr:.2f}"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_rr_vs_outcome_chart(data):
    """Render RR vs Outcome scatter plot"""
    if 'final_outcome' not in data.columns:
        st.info("No outcome data available for RR analysis")
        return
    
    # Filter data with valid RR and outcomes
    scatter_data = data[
        data['rr_planned'].notna() & 
        data['final_outcome'].notna() & 
        (data['final_outcome'] != 'open')
    ].copy()
    
    if scatter_data.empty:
        st.info("No data available for RR vs Outcome analysis")
        return
    
    fig = px.scatter(
        scatter_data,
        x='rr_planned',
        y='pair',
        color='final_outcome',
        title="RR Ratio vs Outcome by Pair",
        labels={'rr_planned': 'Planned RR Ratio', 'pair': 'Trading Pair'},
        hover_data=['signal_id']
    )
    
    fig.update_traces(
        hovertemplate='%{y}<br>RR: %{x:.2f}<br>Outcome: %{marker.color}<br>Signal: %{customdata[0]}<extra></extra>'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_timeline_charts(data):
    """Render timeline analysis charts"""
    if 'created_at' not in data.columns:
        return
    
    # Check if we have valid datetime data
    datetime_data = data[data['created_at'].notna()]
    if datetime_data.empty:
        return
    
    st.subheader("Timeline Analysis")
    
    render_daily_signal_volume(datetime_data)

def render_daily_signal_volume(data):
    """Render daily signal volume chart"""
    # Resample to daily frequency
    daily_signals = data.set_index('created_at').resample('D').size().reset_index()
    daily_signals.columns = ['created_at', 'signal_count']
    
    # Remove days with no signals
    daily_signals = daily_signals[daily_signals['signal_count'] > 0]
    
    if daily_signals.empty:
        st.info("No timeline data available")
        return
    
    fig = px.line(
        daily_signals,
        x='created_at',
        y='signal_count',
        title="Daily Signal Volume",
        markers=True,
        labels={'created_at': 'Date', 'signal_count': 'Number of Signals'}
    )
    
    fig.update_traces(
        hovertemplate='Date: %{x}<br>Signals: %{y}<extra></extra>',
        line=dict(color=CHART_COLORS['primary'], width=2),
        marker=dict(size=6)
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Signal Count",
        hovermode='x'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_outcome_timeline(data):
    """Render outcome timeline if outcome data is available"""
    if 'created_at' not in data.columns or 'final_outcome' not in data.columns:
        return
    
    # Filter closed trades only
    closed_data = data[data['final_outcome'].notna() & (data['final_outcome'] != 'open')]
    
    if closed_data.empty:
        return
    
    # Group by date and outcome
    timeline_data = closed_data.groupby([
        closed_data['created_at'].dt.date,
        'final_outcome'
    ]).size().unstack(fill_value=0)
    
    if timeline_data.empty:
        return
    
    fig = go.Figure()
    
    for outcome in timeline_data.columns:
        fig.add_trace(go.Scatter(
            x=timeline_data.index,
            y=timeline_data[outcome],
            mode='lines+markers',
            name=outcome.upper(),
            stackgroup='one'
        ))
    
    fig.update_layout(
        title="Outcome Timeline (Stacked)",
        xaxis_title="Date",
        yaxis_title="Number of Signals",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
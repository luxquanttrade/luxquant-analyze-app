"""
Top performers components with horizontal bar charts
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config.theme import COLORS, PLOTLY_CONFIG

def render_top_performers(data):
    """Render top performers section"""
    st.markdown("## 🏆 Top Performers")
    
    if 'pair' not in data.columns:
        st.info("No pair data available")
        return
    
    # Calculate pair metrics
    pair_metrics = calculate_pair_metrics(data)
    
    if pair_metrics.empty:
        st.info("No performance data available")
        return
    
    # Create tabs for different metrics
    tab1, tab2, tab3, tab4 = st.tabs(["Top Coins", "Best Win Rate", "Best RR", "Most Active"])
    
    with tab1:
        render_top_coins(pair_metrics)
    
    with tab2:
        render_top_winrate(pair_metrics)
    
    with tab3:
        render_top_rr(pair_metrics)
    
    with tab4:
        render_most_active(pair_metrics)

def calculate_pair_metrics(data):
    """Calculate metrics for each trading pair"""
    metrics_list = []
    
    for pair in data['pair'].unique():
        pair_data = data[data['pair'] == pair]
        
        metrics = {
            'pair': pair,
            'total_signals': len(pair_data),
            'closed_trades': pair_data['final_outcome'].notna().sum() if 'final_outcome' in pair_data.columns else 0
        }
        
        # Win rate calculation
        if metrics['closed_trades'] > 0 and 'final_outcome' in pair_data.columns:
            tp_hits = pair_data['final_outcome'].str.startswith('tp', na=False).sum()
            metrics['win_rate'] = (tp_hits / metrics['closed_trades'] * 100)
            metrics['tp_hits'] = tp_hits
            metrics['sl_hits'] = (pair_data['final_outcome'] == 'sl').sum()
        else:
            metrics['win_rate'] = 0
            metrics['tp_hits'] = 0
            metrics['sl_hits'] = 0
        
        # RR metrics
        if 'rr_planned' in pair_data.columns:
            rr_data = pair_data['rr_planned'].dropna()
            metrics['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
        else:
            metrics['avg_rr'] = 0
        
        # Score calculation (for overall ranking)
        metrics['score'] = calculate_pair_score(metrics)
        
        metrics_list.append(metrics)
    
    return pd.DataFrame(metrics_list)

def calculate_pair_score(metrics):
    """Calculate overall score for ranking"""
    # Weighted scoring: Win rate (40%), Volume (30%), RR (30%)
    wr_score = metrics['win_rate'] * 0.4
    volume_score = min(metrics['total_signals'] / 10, 100) * 0.3  # Normalize to 100
    rr_score = min(metrics['avg_rr'] * 20, 100) * 0.3  # Normalize RR to 100
    
    return wr_score + volume_score + rr_score

def render_top_coins(pair_metrics):
    """Render top coins by overall performance"""
    # Filter and sort
    top_pairs = pair_metrics[pair_metrics['total_signals'] >= 3].nlargest(50, 'score')
    
    if top_pairs.empty:
        st.info("Not enough data")
        return
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Add bars with gradient colors
    colors = [get_score_color(score) for score in top_pairs['score']]
    
    fig.add_trace(go.Bar(
        y=top_pairs['pair'][::-1],  # Reverse for top-to-bottom
        x=top_pairs['score'][::-1],
        orientation='h',
        marker=dict(
            color=colors[::-1],
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        text=[f"{score:.1f}" for score in top_pairs['score'][::-1]],
        textposition='outside',
        textfont=dict(color='white', size=10),
        hovertemplate='%{y}<br>Score: %{x:.1f}<br>Signals: %{customdata}<extra></extra>',
        customdata=top_pairs['total_signals'][::-1]
    ))
    
    fig.update_layout(
        **PLOTLY_CONFIG,
        title="Overall Performance Score (Top 50)",
        xaxis_title="Performance Score",
        yaxis_title="",
        height=max(400, len(top_pairs) * 20),
        xaxis=dict(range=[0, 100]),
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show metrics table for top 10
    st.markdown("### Top 10 Details")
    display_top_table(top_pairs.head(10))

def render_top_winrate(pair_metrics):
    """Render pairs with best win rate"""
    # Filter pairs with minimum trades
    qualified = pair_metrics[pair_metrics['closed_trades'] >= 5].nlargest(20, 'win_rate')
    
    if qualified.empty:
        st.info("Not enough closed trades for analysis")
        return
    
    fig = go.Figure()
    
    # Color based on win rate
    colors = [get_winrate_color(wr) for wr in qualified['win_rate']]
    
    fig.add_trace(go.Bar(
        y=qualified['pair'][::-1],
        x=qualified['win_rate'][::-1],
        orientation='h',
        marker=dict(color=colors[::-1]),
        text=[f"{wr:.1f}%" for wr in qualified['win_rate'][::-1]],
        textposition='outside',
        textfont=dict(color='white', size=10),
        hovertemplate='%{y}<br>Win Rate: %{x:.1f}%<br>Trades: %{customdata}<extra></extra>',
        customdata=qualified['closed_trades'][::-1]
    ))
    
    # Add 50% reference line
    fig.add_vline(x=50, line_dash="dash", line_color=COLORS['text_muted'], opacity=0.5)
    
    fig.update_layout(
        **PLOTLY_CONFIG,
        title="Best Win Rate (Min 5 trades)",
        xaxis_title="Win Rate (%)",
        yaxis_title="",
        height=max(400, len(qualified) * 25),
        xaxis=dict(range=[0, 100]),
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_top_rr(pair_metrics):
    """Render pairs with best RR ratio"""
    # Filter pairs with RR data
    qualified = pair_metrics[pair_metrics['avg_rr'] > 0].nlargest(20, 'avg_rr')
    
    if qualified.empty:
        st.info("No RR data available")
        return
    
    fig = go.Figure()
    
    colors = [get_rr_color(rr) for rr in qualified['avg_rr']]
    
    fig.add_trace(go.Bar(
        y=qualified['pair'][::-1],
        x=qualified['avg_rr'][::-1],
        orientation='h',
        marker=dict(color=colors[::-1]),
        text=[f"{rr:.2f}" for rr in qualified['avg_rr'][::-1]],
        textposition='outside',
        textfont=dict(color='white', size=10),
        hovertemplate='%{y}<br>Avg RR: %{x:.2f}<br>Signals: %{customdata}<extra></extra>',
        customdata=qualified['total_signals'][::-1]
    ))
    
    fig.update_layout(
        **PLOTLY_CONFIG,
        title="Best Risk-Reward Ratios",
        xaxis_title="Average RR Ratio",
        yaxis_title="",
        height=max(400, len(qualified) * 25),
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_most_active(pair_metrics):
    """Render most active trading pairs"""
    top_active = pair_metrics.nlargest(20, 'total_signals')
    
    fig = go.Figure()
    
    # Gradient color based on volume
    max_signals = top_active['total_signals'].max()
    colors = [f"rgba(75, 155, 255, {0.3 + 0.7 * (s/max_signals)})" 
              for s in top_active['total_signals']]
    
    fig.add_trace(go.Bar(
        y=top_active['pair'][::-1],
        x=top_active['total_signals'][::-1],
        orientation='h',
        marker=dict(color=colors[::-1]),
        text=top_active['total_signals'][::-1],
        textposition='outside',
        textfont=dict(color='white', size=10),
        hovertemplate='%{y}<br>Signals: %{x}<br>Win Rate: %{customdata:.1f}%<extra></extra>',
        customdata=top_active['win_rate'][::-1]
    ))
    
    fig.update_layout(
        **PLOTLY_CONFIG,
        title="Most Active Pairs",
        xaxis_title="Total Signals",
        yaxis_title="",
        height=max(400, len(top_active) * 25),
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_top_table(df):
    """Display formatted table for top performers"""
    display_df = df[['pair', 'total_signals', 'win_rate', 'avg_rr', 'score']].copy()
    display_df.columns = ['Pair', 'Signals', 'Win Rate %', 'Avg RR', 'Score']
    
    # Format columns
    display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
    display_df['Avg RR'] = display_df['Avg RR'].apply(lambda x: f"{x:.2f}")
    display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.1f}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=300
    )

def get_score_color(score):
    """Get color based on performance score"""
    if score >= 70:
        return COLORS['green']
    elif score >= 50:
        return COLORS['yellow']
    elif score >= 30:
        return COLORS['blue']
    else:
        return COLORS['red']

def get_winrate_color(winrate):
    """Get color for winrate"""
    if winrate >= 60:
        return COLORS['green']
    elif winrate >= 40:
        return COLORS['yellow']
    else:
        return COLORS['red']

def get_rr_color(rr):
    """Get color for RR ratio"""
    if rr >= 3:
        return COLORS['green']
    elif rr >= 2:
        return COLORS['yellow']
    else:
        return COLORS['red']
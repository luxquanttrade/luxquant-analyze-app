"""
Modern metrics display components with dark theme
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Import theme configurations
try:
    from config.theme import COLORS, PLOTLY_CONFIG, CHART_CONFIGS
except ImportError:
    # Fallback colors if theme file doesn't exist
    COLORS = {
        "green": "#00D46A",
        "red": "#FF4747",
        "yellow": "#FDB32B",
        "blue": "#4B9BFF",
        "purple": "#9D5CFF",
        "text_muted": "#6B6B6B"
    }

def render_summary_cards(data):
    """Render summary metrics in modern card layout"""
    st.markdown("## 📊 Performance Overview")
    
    # Calculate metrics
    metrics = calculate_summary_metrics(data)
    
    # Create 4 columns for main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card(
            "Total Signals",
            f"{metrics['total_signals']:,}",
            f"📈 {metrics['signals_today']} today",
            COLORS['blue']
        )
    
    with col2:
        render_metric_card(
            "Overall Win Rate",
            f"{metrics['win_rate']:.1f}%",
            get_winrate_delta(metrics['win_rate']),
            get_winrate_color(metrics['win_rate'])
        )
    
    with col3:
        render_metric_card(
            "Completion Rate",
            f"{metrics['completion_rate']:.1f}%",
            f"🎯 {metrics['closed_trades']} closed",
            COLORS['purple']
        )
    
    with col4:
        render_metric_card(
            "Avg RR Ratio",
            f"{metrics['avg_rr']:.2f}",
            get_rr_indicator(metrics['avg_rr']),
            get_rr_color(metrics['avg_rr'])
        )
    
    # Second row with additional metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card(
            "Active Pairs",
            f"{metrics['active_pairs']}",
            f"🪙 {metrics['top_pair']}",
            COLORS['yellow']
        )
    
    with col2:
        render_metric_card(
            "TP Hits",
            f"{metrics['tp_hits']:,}",
            f"✅ {metrics['tp_rate']:.1f}%",
            COLORS['green']
        )
    
    with col3:
        render_metric_card(
            "SL Hits", 
            f"{metrics['sl_hits']:,}",
            f"❌ {metrics['sl_rate']:.1f}%",
            COLORS['red']
        )
    
    with col4:
        render_metric_card(
            "Open Signals",
            f"{metrics['open_signals']:,}",
            f"⏳ {metrics['open_rate']:.1f}%",
            COLORS['yellow']
        )

def render_metric_card(label, value, delta, color):
    """Render individual metric card"""
    st.markdown(f"""
    <div class="metric-card">
        <p style="color: #A0A0A0; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 1px;">
            {label}
        </p>
        <h2 style="color: {color}; margin: 8px 0; font-size: 28px; font-weight: 700;">
            {value}
        </h2>
        <p style="color: #6B6B6B; font-size: 11px; margin: 0;">
            {delta}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_winrate_trend(data):
    """Render winrate trend as the main focus"""
    st.markdown("## 📈 Win Rate Trend Analysis")
    
    # Calculate winrate over time
    winrate_data = calculate_winrate_trend(data)
    
    if winrate_data.empty:
        st.info("Not enough data for trend analysis")
        return
    
    # Create the main chart
    fig = go.Figure()
    
    # Add main winrate line
    fig.add_trace(go.Scatter(
        x=winrate_data['date'],
        y=winrate_data['winrate'],
        mode='lines+markers',
        name='Win Rate',
        line=dict(
            color=COLORS['green'],
            width=3
        ),
        marker=dict(
            size=8,
            color=COLORS['green'],
            line=dict(color='white', width=1)
        ),
        fill='tonexty',
        fillcolor='rgba(0, 212, 106, 0.1)'
    ))
    
    # Add 50% reference line
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color=COLORS['text_muted'],
        opacity=0.5,
        annotation_text="Break Even"
    )
    
    # Add moving average
    if len(winrate_data) > 7:
        winrate_data['ma7'] = winrate_data['winrate'].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=winrate_data['date'],
            y=winrate_data['ma7'],
            mode='lines',
            name='7-Day MA',
            line=dict(
                color=COLORS['yellow'],
                width=2,
                dash='dot'
            ),
            opacity=0.7
        ))
    
    # Update layout
    fig.update_layout(
        title=None,
        xaxis_title="Date",
        yaxis_title="Win Rate (%)",
        height=350,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#1A1D24",
        font=dict(color="#FFFFFF", family="Inter, sans-serif"),
        xaxis=dict(
            gridcolor="#2D3139",
            linecolor="#2D3139",
            tickfont=dict(color="#A0A0A0")
        ),
        yaxis=dict(
            range=[0, 100],
            gridcolor="#2D3139",
            linecolor="#2D3139",
            tickfont=dict(color="#A0A0A0")
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add trend summary below chart
    render_trend_summary(winrate_data)

def render_trend_summary(winrate_data):
    """Render trend summary below winrate chart"""
    col1, col2, col3, col4 = st.columns(4)
    
    current_wr = winrate_data['winrate'].iloc[-1]
    avg_wr = winrate_data['winrate'].mean()
    max_wr = winrate_data['winrate'].max()
    min_wr = winrate_data['winrate'].min()
    
    with col1:
        color = get_winrate_color(current_wr)
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="color: #A0A0A0; font-size: 11px;">CURRENT</p>
            <p style="color: {color}; font-size: 20px; font-weight: 700;">{current_wr:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="color: #A0A0A0; font-size: 11px;">AVERAGE</p>
            <p style="color: {COLORS['blue']}; font-size: 20px; font-weight: 700;">{avg_wr:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="color: #A0A0A0; font-size: 11px;">PEAK</p>
            <p style="color: {COLORS['green']}; font-size: 20px; font-weight: 700;">{max_wr:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="color: #A0A0A0; font-size: 11px;">LOWEST</p>
            <p style="color: {COLORS['red']}; font-size: 20px; font-weight: 700;">{min_wr:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

def calculate_summary_metrics(data):
    """Calculate all summary metrics"""
    metrics = {}
    
    # Basic counts
    metrics['total_signals'] = len(data)
    metrics['closed_trades'] = data['final_outcome'].notna().sum() if 'final_outcome' in data.columns else 0
    metrics['open_signals'] = metrics['total_signals'] - metrics['closed_trades']
    
    # Rates
    metrics['completion_rate'] = (metrics['closed_trades'] / metrics['total_signals'] * 100) if metrics['total_signals'] > 0 else 0
    metrics['open_rate'] = 100 - metrics['completion_rate']
    
    # Win/Loss metrics
    if 'final_outcome' in data.columns and metrics['closed_trades'] > 0:
        metrics['tp_hits'] = data['final_outcome'].str.startswith('tp', na=False).sum()
        metrics['sl_hits'] = (data['final_outcome'] == 'sl').sum()
        metrics['win_rate'] = (metrics['tp_hits'] / metrics['closed_trades'] * 100) if metrics['closed_trades'] > 0 else 0
        metrics['tp_rate'] = (metrics['tp_hits'] / metrics['closed_trades'] * 100) if metrics['closed_trades'] > 0 else 0
        metrics['sl_rate'] = (metrics['sl_hits'] / metrics['closed_trades'] * 100) if metrics['closed_trades'] > 0 else 0
    else:
        metrics['tp_hits'] = 0
        metrics['sl_hits'] = 0
        metrics['win_rate'] = 0
        metrics['tp_rate'] = 0
        metrics['sl_rate'] = 0
    
    # RR metrics
    if 'rr_planned' in data.columns:
        rr_data = data['rr_planned'].dropna()
        metrics['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
    else:
        metrics['avg_rr'] = 0
    
    # Pair metrics
    if 'pair' in data.columns:
        metrics['active_pairs'] = data['pair'].nunique()
        metrics['top_pair'] = data['pair'].value_counts().index[0] if not data['pair'].empty else "N/A"
    else:
        metrics['active_pairs'] = 0
        metrics['top_pair'] = "N/A"
    
    # Today's signals
    if 'created_at' in data.columns:
        today = pd.Timestamp.now().date()
        data['created_date'] = pd.to_datetime(data['created_at']).dt.date
        metrics['signals_today'] = (data['created_date'] == today).sum()
    else:
        metrics['signals_today'] = 0
    
    return metrics

def calculate_winrate_trend(data):
    """Calculate winrate trend over time"""
    if 'created_at' not in data.columns or 'final_outcome' not in data.columns:
        return pd.DataFrame()
    
    # Filter closed trades
    closed_data = data[data['final_outcome'].notna()].copy()
    if closed_data.empty:
        return pd.DataFrame()
    
    # Add date and winner flag
    closed_data['date'] = pd.to_datetime(closed_data['created_at'], errors='coerce').dt.date
    closed_data['is_winner'] = closed_data['final_outcome'].str.startswith('tp', na=False)
    
    # Filter out invalid dates
    closed_data = closed_data[closed_data['date'].notna()]
    
    if closed_data.empty:
        return pd.DataFrame()
    
    # Group by date
    daily_stats = closed_data.groupby('date').agg({
        'is_winner': ['sum', 'count']
    }).reset_index()
    
    daily_stats.columns = ['date', 'wins', 'total']
    daily_stats['winrate'] = (daily_stats['wins'] / daily_stats['total'] * 100).round(2)
    
    return daily_stats

def get_winrate_color(winrate):
    """Get color based on winrate"""
    if winrate >= 60:
        return COLORS['green']
    elif winrate >= 40:
        return COLORS['yellow']
    else:
        return COLORS['red']

def get_winrate_delta(winrate):
    """Get winrate delta indicator"""
    if winrate >= 60:
        return "🔥 Excellent"
    elif winrate >= 50:
        return "✅ Good"
    elif winrate >= 40:
        return "⚠️ Below average"
    else:
        return "⚠️ Needs improvement"

def get_rr_color(rr):
    """Get color based on RR ratio"""
    if rr >= 3:
        return COLORS['green']
    elif rr >= 2:
        return COLORS['yellow']
    else:
        return COLORS['red']

def get_rr_indicator(rr):
    """Get RR indicator text"""
    if rr >= 3:
        return "🎯 Excellent"
    elif rr >= 2:
        return "👍 Good"
    elif rr >= 1:
        return "⚠️ Low"
    else:
        return "❌ Very Low"
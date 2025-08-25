"""
Fixed Top performers components with resolved Plotly layout conflicts
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Safe theme import with fallbacks
try:
    from config.theme import COLORS, PLOTLY_CONFIG
except ImportError:
    COLORS = {
        "green": "#00D46A",
        "red": "#FF4747",
        "yellow": "#FDB32B",
        "blue": "#4B9BFF",
        "purple": "#9D5CFF",
        "text_muted": "#6B6B6B"
    }
    PLOTLY_CONFIG = {}

def render_top_performers(data):
    """Render top performers section with enhanced error handling"""
    st.markdown("## 🏆 Top Performers")
    
    if data is None or data.empty:
        st.warning("No data available for top performers analysis")
        return
    
    if 'pair' not in data.columns:
        st.info("No pair data available")
        return
    
    try:
        # Calculate pair metrics with error handling
        pair_metrics = calculate_pair_metrics_safe(data)
        
        if pair_metrics.empty:
            st.info("No performance data available")
            return
        
        # Create tabs for different metrics
        tab1, tab2, tab3, tab4 = st.tabs(["🏅 Top Coins", "📈 Best Win Rate", "🎯 Best RR", "⚡ Most Active"])
        
        with tab1:
            render_top_coins_safe(pair_metrics)
        
        with tab2:
            render_top_winrate_safe(pair_metrics)
        
        with tab3:
            render_top_rr_safe(pair_metrics)
        
        with tab4:
            render_most_active_safe(pair_metrics)
            
    except Exception as e:
        st.error(f"❌ Top performers rendering failed: {e}")
        st.info("💡 This might be due to data formatting issues. Check the data structure.")

def calculate_pair_metrics_safe(data):
    """Calculate metrics for each trading pair with comprehensive error handling"""
    try:
        if data is None or data.empty or 'pair' not in data.columns:
            return pd.DataFrame()
        
        st.info(f"📊 Calculating metrics for {data['pair'].nunique()} unique pairs...")
        
        metrics_list = []
        
        for pair in data['pair'].unique():
            if pd.isna(pair) or pair == 'UNKNOWN':
                continue
                
            pair_data = data[data['pair'] == pair]
            
            if pair_data.empty:
                continue
            
            metrics = {
                'pair': pair,
                'total_signals': len(pair_data),
                'closed_trades': 0,
                'win_rate': 0,
                'tp_hits': 0,
                'sl_hits': 0,
                'avg_rr': 0,
                'score': 0
            }
            
            # Calculate closed trades
            if 'final_outcome' in pair_data.columns:
                closed_data = pair_data[
                    pair_data['final_outcome'].notna() & 
                    (pair_data['final_outcome'] != 'open') &
                    (pair_data['final_outcome'] != '')
                ]
                metrics['closed_trades'] = len(closed_data)
                
                # Win rate calculation
                if metrics['closed_trades'] > 0:
                    tp_hits = closed_data['final_outcome'].str.startswith('tp', na=False).sum()
                    metrics['tp_hits'] = tp_hits
                    metrics['sl_hits'] = (closed_data['final_outcome'] == 'sl').sum()
                    metrics['win_rate'] = (tp_hits / metrics['closed_trades'] * 100)
            
            # RR metrics
            if 'rr_planned' in pair_data.columns:
                rr_data = pair_data['rr_planned'].dropna()
                metrics['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
            
            # Score calculation (for overall ranking)
            metrics['score'] = calculate_pair_score_safe(metrics)
            
            metrics_list.append(metrics)
        
        result_df = pd.DataFrame(metrics_list)
        st.success(f"✅ Calculated metrics for {len(result_df)} pairs")
        
        return result_df
        
    except Exception as e:
        st.error(f"❌ Pair metrics calculation failed: {e}")
        return pd.DataFrame()

def calculate_pair_score_safe(metrics):
    """Calculate overall score for ranking with safe handling"""
    try:
        # Weighted scoring: Win rate (40%), Volume (30%), RR (30%)
        wr_score = metrics.get('win_rate', 0) * 0.4
        volume_score = min(metrics.get('total_signals', 0) / 10, 100) * 0.3
        rr_score = min(metrics.get('avg_rr', 0) * 20, 100) * 0.3
        
        return wr_score + volume_score + rr_score
    except:
        return 0

def render_top_coins_safe(pair_metrics):
    """Render top coins by overall performance with fixed Plotly layout"""
    try:
        if pair_metrics.empty:
            st.info("No data available for top coins analysis")
            return
        
        # Filter and sort
        top_pairs = pair_metrics[pair_metrics['total_signals'] >= 3].nlargest(20, 'score')
        
        if top_pairs.empty:
            st.info("Not enough data (minimum 3 signals required)")
            return
        
        # Create horizontal bar chart with fixed layout
        fig = go.Figure()
        
        # Add bars
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
        
        # Fixed layout - avoid duplicate xaxis parameter
        layout_config = {
            "template": "plotly_dark",
            "paper_bgcolor": "#1A1D24",
            "plot_bgcolor": "#1A1D24",
            "title": {
                "text": "Overall Performance Score (Top 20)",
                "font": {"color": "#FFFFFF", "size": 16}
            },
            "font": {"color": "#FFFFFF"},
            "height": max(400, len(top_pairs) * 25),
            "margin": {"l": 100, "r": 50, "t": 60, "b": 50}
        }
        
        # Set axis properties separately to avoid conflicts
        layout_config["xaxis"] = {
            "title": "Performance Score",
            "range": [0, 100],
            "gridcolor": "#2D3139",
            "tickfont": {"color": "#A0A0A0"}
        }
        
        layout_config["yaxis"] = {
            "title": "",
            "gridcolor": "#2D3139",
            "tickfont": {"color": "#A0A0A0"}
        }
        
        fig.update_layout(**layout_config)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show metrics table for top 10
        st.markdown("### 📊 Top 10 Details")
        display_top_table_safe(top_pairs.head(10))
        
    except Exception as e:
        st.error(f"❌ Top coins rendering failed: {e}")
        render_fallback_table(pair_metrics, "score", "Top Performing Coins")

def render_top_winrate_safe(pair_metrics):
    """Render pairs with best win rate - fixed layout"""
    try:
        if pair_metrics.empty:
            st.info("No data available for win rate analysis")
            return
        
        # Filter pairs with minimum trades
        qualified = pair_metrics[pair_metrics['closed_trades'] >= 5].nlargest(15, 'win_rate')
        
        if qualified.empty:
            st.info("Not enough closed trades for analysis (minimum 5 required)")
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
        
        # Fixed layout
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            title={
                "text": "Best Win Rate (Min 5 trades)",
                "font": {"color": "#FFFFFF", "size": 16}
            },
            xaxis={
                "title": "Win Rate (%)",
                "range": [0, 100],
                "gridcolor": "#2D3139"
            },
            yaxis={
                "title": "",
                "gridcolor": "#2D3139"
            },
            font={"color": "#FFFFFF"},
            height=max(400, len(qualified) * 25),
            margin={"l": 100, "r": 50, "t": 60, "b": 50}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Win rate chart failed: {e}")
        render_fallback_table(qualified if 'qualified' in locals() else pair_metrics, "win_rate", "Best Win Rate")

def render_top_rr_safe(pair_metrics):
    """Render pairs with best RR ratio - fixed layout"""
    try:
        if pair_metrics.empty:
            st.info("No data available for RR analysis")
            return
        
        # Filter pairs with RR data
        qualified = pair_metrics[pair_metrics['avg_rr'] > 0].nlargest(15, 'avg_rr')
        
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
        
        # Fixed layout
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            title={
                "text": "Best Risk-Reward Ratios",
                "font": {"color": "#FFFFFF", "size": 16}
            },
            xaxis={
                "title": "Average RR Ratio",
                "gridcolor": "#2D3139"
            },
            yaxis={
                "title": "",
                "gridcolor": "#2D3139"
            },
            font={"color": "#FFFFFF"},
            height=max(400, len(qualified) * 25),
            margin={"l": 100, "r": 50, "t": 60, "b": 50}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ RR chart failed: {e}")
        render_fallback_table(qualified if 'qualified' in locals() else pair_metrics, "avg_rr", "Best RR Ratios")

def render_most_active_safe(pair_metrics):
    """Render most active trading pairs - fixed layout"""
    try:
        if pair_metrics.empty:
            st.info("No data available for activity analysis")
            return
        
        top_active = pair_metrics.nlargest(15, 'total_signals')
        
        if top_active.empty:
            st.info("No activity data available")
            return
        
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
        
        # Fixed layout
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            title={
                "text": "Most Active Pairs",
                "font": {"color": "#FFFFFF", "size": 16}
            },
            xaxis={
                "title": "Total Signals",
                "gridcolor": "#2D3139"
            },
            yaxis={
                "title": "",
                "gridcolor": "#2D3139"
            },
            font={"color": "#FFFFFF"},
            height=max(400, len(top_active) * 25),
            margin={"l": 100, "r": 50, "t": 60, "b": 50}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Activity chart failed: {e}")
        render_fallback_table(top_active if 'top_active' in locals() else pair_metrics, "total_signals", "Most Active Pairs")

def display_top_table_safe(df):
    """Display formatted table for top performers with error handling"""
    try:
        if df.empty:
            st.info("No data to display")
            return
        
        display_df = df[['pair', 'total_signals', 'win_rate', 'avg_rr', 'score']].copy()
        display_df.columns = ['Pair', 'Signals', 'Win Rate %', 'Avg RR', 'Score']
        
        # Format columns safely
        display_df['Win Rate %'] = display_df['Win Rate %'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        display_df['Avg RR'] = display_df['Avg RR'].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
        )
        display_df['Score'] = display_df['Score'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=300
        )
        
    except Exception as e:
        st.error(f"❌ Table display failed: {e}")

def render_fallback_table(df, sort_column, title):
    """Render fallback table when charts fail"""
    try:
        st.markdown(f"### 📋 {title} (Table View)")
        
        if df.empty:
            st.info("No data available")
            return
        
        # Sort and display top 10
        if sort_column in df.columns:
            top_df = df.nlargest(10, sort_column)
        else:
            top_df = df.head(10)
        
        # Select relevant columns
        display_cols = ['pair', 'total_signals', 'win_rate', 'avg_rr']
        available_cols = [col for col in display_cols if col in top_df.columns]
        
        if available_cols:
            display_df = top_df[available_cols].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.error("No suitable columns found for display")
            
    except Exception as e:
        st.error(f"❌ Fallback table failed: {e}")

def get_score_color(score):
    """Get color based on performance score"""
    try:
        if score >= 70:
            return COLORS['green']
        elif score >= 50:
            return COLORS['yellow']
        elif score >= 30:
            return COLORS['blue']
        else:
            return COLORS['red']
    except:
        return "#4B9BFF"  # Default blue

def get_winrate_color(winrate):
    """Get color for winrate"""
    try:
        if winrate >= 60:
            return COLORS['green']
        elif winrate >= 40:
            return COLORS['yellow']
        else:
            return COLORS['red']
    except:
        return "#FDB32B"  # Default yellow

def get_rr_color(rr):
    """Get color for RR ratio"""
    try:
        if rr >= 3:
            return COLORS['green']
        elif rr >= 2:
            return COLORS['yellow']
        else:
            return COLORS['red']
    except:
        return "#FDB32B"  # Default yellow
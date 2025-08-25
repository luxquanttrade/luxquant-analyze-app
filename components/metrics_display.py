"""
Performance metrics display components
"""
import streamlit as st
import pandas as pd
from data_processing.metrics_calculator import calculate_portfolio_metrics, calculate_pair_metrics
from utils.helpers import format_number, format_percentage

def render_performance_summary(data):
    """Render the main performance summary section"""
    st.markdown("---")
    st.subheader("Performance Summary")
    
    if data is None or data.empty:
        st.warning("No data available for performance summary")
        return
    
    # Calculate portfolio metrics
    metrics = calculate_portfolio_metrics(data)
    
    # Display main metrics in columns
    render_main_metrics(metrics)
    
    # Additional metrics section
    render_additional_metrics(data, metrics)

def render_main_metrics(metrics):
    """Render main metrics in columns"""
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Signals", f"{metrics.get('total_signals', 0):,}")
    
    with col2:
        st.metric("Closed Trades", f"{metrics.get('closed_trades', 0):,}")
    
    with col3:
        win_rate = metrics.get('win_rate', 0)
        st.metric("Win Rate", format_percentage(win_rate))
    
    with col4:
        st.metric("TP Hits", f"{metrics.get('tp_hits', 0):,}")
    
    with col5:
        st.metric("SL Hits", f"{metrics.get('sl_hits', 0):,}")
    
    with col6:
        avg_rr = metrics.get('avg_rr_planned', 0)
        st.metric("Avg RR", format_number(avg_rr, 2))

def render_additional_metrics(data, metrics):
    """Render additional metrics below main metrics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Portfolio Stats**")
        st.write(f"• Open Signals: {metrics.get('open_signals', 0):,}")
        st.write(f"• Unique Pairs: {data['pair'].nunique() if 'pair' in data.columns else 0}")
        
        # Date range if available
        if 'created_at' in data.columns and data['created_at'].notna().any():
            date_min = data['created_at'].min().date()
            date_max = data['created_at'].max().date()
            st.write(f"• Date Range: {date_min} to {date_max}")
    
    with col2:
        st.markdown("**Risk-Reward Stats**")
        if 'rr_planned' in data.columns:
            rr_data = data['rr_planned'].dropna()
            if len(rr_data) > 0:
                st.write(f"• Min RR: {format_number(rr_data.min(), 1)}")
                st.write(f"• Max RR: {format_number(rr_data.max(), 1)}")
                st.write(f"• Median RR: {format_number(rr_data.median(), 2)}")
            else:
                st.write("• No RR data available")
        else:
            st.write("• RR metrics not calculated")
    
    with col3:
        st.markdown("**Performance Stats**")
        if 'rr_realized' in data.columns:
            realized_data = data['rr_realized'].dropna()
            if len(realized_data) > 0:
                st.write(f"• Avg Realized RR: {format_number(realized_data.mean(), 2)}")
                st.write(f"• Total Realized RR: {format_number(realized_data.sum(), 2)}")
            else:
                st.write("• No realized RR data")
        else:
            st.write("• Realized metrics not available")

def render_pair_performance(data):
    """Render performance by trading pair section"""
    if data is None or data.empty or 'pair' not in data.columns:
        return
    
    if data['pair'].nunique() <= 1:
        return
    
    st.subheader("Performance by Trading Pair")
    
    # Calculate pair metrics
    pair_metrics = calculate_pair_metrics(data)
    
    if pair_metrics.empty:
        st.warning("No pair performance data available")
        return
    
    # Filter pairs with minimum signals (3)
    min_signals = 3
    filtered_pairs = pair_metrics[pair_metrics['total_signals'] >= min_signals].copy()
    
    if filtered_pairs.empty:
        st.info(f"No pairs with minimum {min_signals} signals found")
        return
    
    # Format the display dataframe
    display_df = format_pair_metrics(filtered_pairs)
    
    # Display the table
    st.dataframe(display_df, use_container_width=True)
    
    # Show pair performance insights
    render_pair_insights(filtered_pairs)

def format_pair_metrics(pair_metrics):
    """Format pair metrics for display"""
    display_df = pair_metrics.copy()
    
    # Select and order columns
    display_cols = ['pair', 'total_signals', 'tp_hits', 'sl_hits', 'win_rate', 'avg_rr_planned']
    available_cols = [col for col in display_cols if col in display_df.columns]
    display_df = display_df[available_cols]
    
    # Format numeric columns
    if 'win_rate' in display_df.columns:
        display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    
    if 'avg_rr_planned' in display_df.columns:
        display_df['avg_rr_planned'] = display_df['avg_rr_planned'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    # Rename columns for display
    column_names = {
        'pair': 'Trading Pair',
        'total_signals': 'Total Signals',
        'tp_hits': 'TP Hits',
        'sl_hits': 'SL Hits',
        'win_rate': 'Win Rate',
        'avg_rr_planned': 'Avg RR'
    }
    
    display_df = display_df.rename(columns=column_names)
    
    return display_df

def render_pair_insights(pair_metrics):
    """Render insights about pair performance"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Performers**")
        if 'win_rate' in pair_metrics.columns:
            top_pairs = pair_metrics.nlargest(3, 'win_rate')
            for _, row in top_pairs.iterrows():
                win_rate = row.get('win_rate', 0)
                st.write(f"• {row['pair']}: {win_rate:.1f}% win rate")
        else:
            st.write("Win rate data not available")
    
    with col2:
        st.markdown("**Most Active**")
        if 'total_signals' in pair_metrics.columns:
            active_pairs = pair_metrics.nlargest(3, 'total_signals')
            for _, row in active_pairs.iterrows():
                total = row.get('total_signals', 0)
                st.write(f"• {row['pair']}: {total} signals")
        else:
            st.write("Signal count data not available")

def render_quick_stats(data):
    """Render quick statistics section"""
    if data is None or data.empty:
        return
    
    st.markdown("**Quick Stats**")
    
    stats = []
    
    # Pair count
    if 'pair' in data.columns:
        stats.append(f"**Total Pairs:** {data['pair'].nunique()}")
    
    # Date range
    if 'created_at' in data.columns and data['created_at'].notna().any():
        date_min = data['created_at'].min().date()
        date_max = data['created_at'].max().date()
        stats.append(f"**Date Range:** {date_min} to {date_max}")
    
    # Open signals
    if 'is_open' in data.columns:
        open_count = data['is_open'].sum()
        stats.append(f"**Open Signals:** {open_count:,}")
    
    # RR range
    if 'rr_planned' in data.columns:
        rr_data = data['rr_planned'].dropna()
        if len(rr_data) > 0:
            stats.append(f"**RR Range:** {rr_data.min():.1f} - {rr_data.max():.1f}")
    
    # Display stats
    for stat in stats:
        st.write(stat)
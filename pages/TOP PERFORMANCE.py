"""
🏆 Top Performance - LuxQuant Pro
Comprehensive analysis of top performing trading pairs with detailed metrics
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
    page_title="🏆 Top Performance - LuxQuant Pro",
    page_icon="🏆",
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
        "yellow": "#FDB32B",
        "purple": "#9D5CFF",
        "background": "#0E1117"
    }

def render_page_header():
    """Render page header"""
    st.markdown("""
    <div style="margin-bottom: 30px;">
        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">
            🏆 Top Performance
        </h1>
        <p style="color: #A0A0A0; font-size: 16px; margin-top: 10px;">
            Comprehensive analysis of top performing trading pairs with detailed metrics and insights
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_performance_filters():
    """Render performance analysis filters"""
    st.sidebar.title("🏆 Performance Analysis")
    
    filters = {}
    
    # Time Range Filter
    st.sidebar.subheader("📅 Time Range")
    time_range = st.sidebar.selectbox(
        "Analysis Period",
        ["All Time", "Year to Date", "Month to Date", "Last 30 Days", "Last 7 Days"],
        help="Select time range for performance analysis"
    )
    
    # Map time range
    time_range_map = {
        "All Time": "all",
        "Year to Date": "ytd", 
        "Month to Date": "mtd",
        "Last 30 Days": "30d",
        "Last 7 Days": "7d"
    }
    filters['time_range'] = time_range_map[time_range]
    
    # Minimum trades filter
    st.sidebar.subheader("📊 Criteria")
    filters['min_trades'] = st.sidebar.slider(
        "Minimum Trades",
        min_value=1,
        max_value=50,
        value=5,
        help="Minimum number of closed trades to qualify for ranking"
    )
    
    # Top N selector
    filters['top_n'] = st.sidebar.selectbox(
        "Show Top N Coins",
        [10, 15, 20, 25, 30],
        index=2,  # Default to 20
        help="Number of top performers to display"
    )
    
    # Metric selector
    filters['sort_metric'] = st.sidebar.radio(
        "Rank by Metric",
        ["Win Rate", "Total Signals", "RR Ratio", "Performance Score"],
        help="Primary metric for ranking coins"
    )
    
    return filters

def calculate_comprehensive_metrics(data, filters):
    """Calculate comprehensive metrics for all pairs"""
    if data is None or data.empty:
        return pd.DataFrame()
    
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
    
    if filtered_data.empty:
        return pd.DataFrame()
    
    st.info(f"📊 Analyzing {filtered_data['pair'].nunique()} unique pairs...")
    
    # Calculate metrics for each pair
    pair_metrics = []
    
    for pair in filtered_data['pair'].unique():
        if pd.isna(pair):
            continue
            
        pair_data = filtered_data[filtered_data['pair'] == pair]
        
        metrics = {
            'pair': pair,
            'total_signals': len(pair_data),
            'closed_trades': 0,
            'open_signals': 0,
            'win_rate': 0,
            'tp1_count': 0,
            'tp2_count': 0,
            'tp3_count': 0,
            'tp4_count': 0,
            'sl_count': 0,
            'avg_rr': 0,
            'performance_score': 0
        }
        
        # Closed trades analysis
        if 'final_outcome' in pair_data.columns:
            closed_data = pair_data[
                pair_data['final_outcome'].notna() & 
                (pair_data['final_outcome'] != 'open')
            ]
            metrics['closed_trades'] = len(closed_data)
            metrics['open_signals'] = metrics['total_signals'] - metrics['closed_trades']
            
            if metrics['closed_trades'] > 0:
                # TP level counts
                metrics['tp1_count'] = (closed_data['final_outcome'] == 'tp1').sum()
                metrics['tp2_count'] = (closed_data['final_outcome'] == 'tp2').sum()
                metrics['tp3_count'] = (closed_data['final_outcome'] == 'tp3').sum()
                metrics['tp4_count'] = (closed_data['final_outcome'] == 'tp4').sum()
                metrics['sl_count'] = (closed_data['final_outcome'] == 'sl').sum()
                
                # Win rate
                total_tp = metrics['tp1_count'] + metrics['tp2_count'] + metrics['tp3_count'] + metrics['tp4_count']
                metrics['win_rate'] = (total_tp / metrics['closed_trades'] * 100)
        
        # RR analysis
        if 'rr_planned' in pair_data.columns:
            rr_data = pair_data['rr_planned'].dropna()
            metrics['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
        
        # Performance score (weighted combination)
        metrics['performance_score'] = calculate_performance_score(metrics)
        
        pair_metrics.append(metrics)
    
    result_df = pd.DataFrame(pair_metrics)
    
    # Filter by minimum trades
    min_trades = filters.get('min_trades', 5)
    qualified_pairs = result_df[result_df['closed_trades'] >= min_trades].copy()
    
    st.success(f"✅ Found {len(qualified_pairs)} pairs with minimum {min_trades} trades")
    
    return qualified_pairs

def calculate_performance_score(metrics):
    """Calculate overall performance score"""
    try:
        # Weighted scoring system
        win_rate_score = metrics.get('win_rate', 0) * 0.4  # 40% weight
        volume_score = min(metrics.get('total_signals', 0) / 20 * 100, 100) * 0.3  # 30% weight
        rr_score = min(metrics.get('avg_rr', 0) / 5 * 100, 100) * 0.3  # 30% weight
        
        return win_rate_score + volume_score + rr_score
    except:
        return 0

def render_top_performers_overview(metrics_df, filters):
    """Render top performers overview"""
    if metrics_df.empty:
        st.warning("No qualified pairs found for analysis")
        return
    
    # Sort by selected metric
    sort_metric_map = {
        "Win Rate": "win_rate",
        "Total Signals": "total_signals", 
        "RR Ratio": "avg_rr",
        "Performance Score": "performance_score"
    }
    
    sort_column = sort_metric_map[filters.get('sort_metric', 'Win Rate')]
    top_n = filters.get('top_n', 20)
    
    top_performers = metrics_df.nlargest(top_n, sort_column)
    
    # Render overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏅 Top Performer",
            top_performers.iloc[0]['pair'],
            f"{top_performers.iloc[0]['win_rate']:.1f}% WR"
        )
    
    with col2:
        avg_wr = top_performers['win_rate'].mean()
        st.metric(
            "📊 Average WR (Top 20)",
            f"{avg_wr:.1f}%",
            f"{len(top_performers)} pairs"
        )
    
    with col3:
        total_signals = top_performers['total_signals'].sum()
        st.metric(
            "📈 Total Signals",
            f"{total_signals:,}",
            "Combined volume"
        )
    
    with col4:
        avg_rr = top_performers['avg_rr'].mean()
        st.metric(
            "⚖️ Average RR",
            f"{avg_rr:.2f}",
            "Risk-reward ratio"
        )
    
    return top_performers

def render_performance_charts(top_performers, filters):
    """Render comprehensive performance charts"""
    if top_performers.empty:
        return
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🏅 Overall Ranking", "📊 Win Rate Focus", "🎯 TP Level Breakdown", "⚖️ RR Analysis"])
    
    with tab1:
        render_overall_performance_chart(top_performers, filters)
    
    with tab2:
        render_winrate_focused_chart(top_performers)
    
    with tab3:
        render_tp_breakdown_analysis(top_performers)
    
    with tab4:
        render_rr_performance_chart(top_performers)

def render_overall_performance_chart(top_performers, filters):
    """Render main performance ranking chart"""
    st.subheader("🏅 Overall Performance Ranking")
    
    # Get sort metric for coloring
    sort_metric = filters.get('sort_metric', 'Win Rate')
    metric_map = {
        "Win Rate": "win_rate",
        "Total Signals": "total_signals",
        "RR Ratio": "avg_rr", 
        "Performance Score": "performance_score"
    }
    
    color_column = metric_map[sort_metric]
    
    # Create horizontal bar chart
    fig = go.Figure(data=[go.Bar(
        y=top_performers['pair'][::-1],
        x=top_performers[color_column][::-1],
        orientation='h',
        marker=dict(
            color=top_performers[color_column][::-1],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=sort_metric)
        ),
        text=[f"{val:.1f}" + ("%" if sort_metric == "Win Rate" else "") 
              for val in top_performers[color_column][::-1]],
        textposition='outside',
        textfont=dict(color='white', size=10),
        hovertemplate='<b>%{y}</b><br>' + 
                     f'{sort_metric}: %{{x:.1f}}' + ("%" if sort_metric == "Win Rate" else "") + '<br>' +
                     'Signals: %{customdata[0]}<br>' +
                     'Win Rate: %{customdata[1]:.1f}%<br>' +
                     'RR: %{customdata[2]:.2f}<extra></extra>',
        customdata=list(zip(
            top_performers['total_signals'][::-1],
            top_performers['win_rate'][::-1],
            top_performers['avg_rr'][::-1]
        ))
    )])
    
    fig.update_layout(
        title=f"Top {len(top_performers)} Pairs by {sort_metric}",
        xaxis_title=sort_metric + (" (%)" if sort_metric == "Win Rate" else ""),
        yaxis_title="Trading Pair",
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#1A1D24",
        font=dict(color="#FFFFFF"),
        height=max(600, len(top_performers) * 25),
        margin=dict(l=100, r=100, t=60, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_winrate_focused_chart(top_performers):
    """Render win rate focused analysis"""
    st.subheader("📊 Win Rate Performance")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Win rate distribution
        fig = go.Figure(data=[go.Histogram(
            x=top_performers['win_rate'],
            nbinsx=15,
            marker_color=COLORS['green'],
            opacity=0.7
        )])
        
        fig.add_vline(
            x=top_performers['win_rate'].mean(),
            line_dash="dash",
            line_color=COLORS['yellow'],
            annotation_text=f"Mean: {top_performers['win_rate'].mean():.1f}%"
        )
        
        fig.add_vline(
            x=50,
            line_dash="dash",
            line_color=COLORS['red'],
            annotation_text="Break Even: 50%"
        )
        
        fig.update_layout(
            title="Win Rate Distribution",
            xaxis_title="Win Rate (%)",
            yaxis_title="Number of Pairs",
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Win rate categories
        st.markdown("**🎯 Performance Categories:**")
        
        excellent = (top_performers['win_rate'] >= 70).sum()
        good = ((top_performers['win_rate'] >= 60) & (top_performers['win_rate'] < 70)).sum()
        average = ((top_performers['win_rate'] >= 50) & (top_performers['win_rate'] < 60)).sum()
        poor = (top_performers['win_rate'] < 50).sum()
        
        st.metric("🔥 Excellent (≥70%)", f"{excellent} pairs")
        st.metric("✅ Good (60-69%)", f"{good} pairs")  
        st.metric("⚠️ Average (50-59%)", f"{average} pairs")
        st.metric("❌ Poor (<50%)", f"{poor} pairs")
        
        # Best performers list
        st.markdown("**🏅 Top 5 by Win Rate:**")
        top_5_wr = top_performers.nlargest(5, 'win_rate')
        for i, (_, row) in enumerate(top_5_wr.iterrows(), 1):
            st.write(f"{i}. **{row['pair']}** - {row['win_rate']:.1f}%")

def render_tp_breakdown_analysis(top_performers):
    """Render TP level breakdown analysis"""
    st.subheader("🎯 Take Profit Level Analysis")
    
    if not any(col in top_performers.columns for col in ['tp1_count', 'tp2_count', 'tp3_count', 'tp4_count']):
        st.info("No TP level data available")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Stacked bar chart of TP levels
        fig = go.Figure()
        
        # Add traces for each TP level
        tp_levels = ['tp1_count', 'tp2_count', 'tp3_count', 'tp4_count']
        tp_labels = ['TP1', 'TP2', 'TP3', 'TP4']
        colors = [COLORS['green'], COLORS['blue'], COLORS['yellow'], COLORS['purple']]
        
        for tp_level, label, color in zip(tp_levels, tp_labels, colors):
            if tp_level in top_performers.columns:
                fig.add_trace(go.Bar(
                    name=label,
                    y=top_performers['pair'][:15][::-1],  # Top 15 for readability
                    x=top_performers[tp_level][:15][::-1],
                    orientation='h',
                    marker_color=color,
                    offsetgroup=1
                ))
        
        fig.update_layout(
            title="TP Level Breakdown (Top 15 Pairs)",
            xaxis_title="Number of Hits",
            yaxis_title="Trading Pair",
            barmode='stack',
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # TP level statistics
        st.markdown("**📊 TP Level Statistics:**")
        
        total_tp1 = top_performers['tp1_count'].sum()
        total_tp2 = top_performers['tp2_count'].sum() 
        total_tp3 = top_performers['tp3_count'].sum()
        total_tp4 = top_performers['tp4_count'].sum()
        total_tp = total_tp1 + total_tp2 + total_tp3 + total_tp4
        
        if total_tp > 0:
            st.metric("🥇 TP1 Hits", f"{total_tp1} ({total_tp1/total_tp*100:.1f}%)")
            st.metric("🥈 TP2 Hits", f"{total_tp2} ({total_tp2/total_tp*100:.1f}%)")
            st.metric("🥉 TP3 Hits", f"{total_tp3} ({total_tp3/total_tp*100:.1f}%)")
            st.metric("🏆 TP4 Hits", f"{total_tp4} ({total_tp4/total_tp*100:.1f}%)")
        
        # Best TP4 performers
        st.markdown("**🏆 Best TP4 Performers:**")
        best_tp4 = top_performers[top_performers['tp4_count'] > 0].nlargest(5, 'tp4_count')
        for _, row in best_tp4.iterrows():
            st.write(f"• **{row['pair']}**: {row['tp4_count']} TP4 hits")

def render_rr_performance_chart(top_performers):
    """Render risk-reward performance analysis"""
    st.subheader("⚖️ Risk-Reward Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Scatter plot: Win Rate vs RR Ratio
        fig = px.scatter(
            top_performers,
            x='avg_rr',
            y='win_rate',
            size='total_signals',
            color='performance_score',
            hover_name='pair',
            title="Win Rate vs Risk-Reward Ratio",
            labels={
                'avg_rr': 'Average RR Ratio',
                'win_rate': 'Win Rate (%)',
                'total_signals': 'Total Signals',
                'performance_score': 'Performance Score'
            },
            color_continuous_scale='Viridis'
        )
        
        # Add reference lines
        fig.add_hline(y=50, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_vline(x=2, line_dash="dash", line_color="orange", opacity=0.5)
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # RR categories and best performers
        st.markdown("**⚖️ RR Categories:**")
        
        excellent_rr = (top_performers['avg_rr'] >= 3).sum()
        good_rr = ((top_performers['avg_rr'] >= 2) & (top_performers['avg_rr'] < 3)).sum()
        average_rr = ((top_performers['avg_rr'] >= 1) & (top_performers['avg_rr'] < 2)).sum()
        poor_rr = (top_performers['avg_rr'] < 1).sum()
        
        st.metric("🚀 Excellent (≥3.0)", f"{excellent_rr} pairs")
        st.metric("👍 Good (2.0-2.9)", f"{good_rr} pairs")
        st.metric("⚠️ Average (1.0-1.9)", f"{average_rr} pairs") 
        st.metric("📉 Poor (<1.0)", f"{poor_rr} pairs")
        
        # Best RR performers
        st.markdown("**🎯 Best RR Performers:**")
        best_rr = top_performers.nlargest(5, 'avg_rr')
        for _, row in best_rr.iterrows():
            st.write(f"• **{row['pair']}**: {row['avg_rr']:.2f} RR")

def render_detailed_table(top_performers):
    """Render detailed performance table"""
    st.subheader("📋 Detailed Performance Table")
    
    # Prepare display dataframe
    display_df = top_performers.copy()
    
    # Select and rename columns
    columns_to_show = {
        'pair': 'Trading Pair',
        'total_signals': 'Total Signals',
        'closed_trades': 'Closed Trades', 
        'win_rate': 'Win Rate (%)',
        'tp1_count': 'TP1',
        'tp2_count': 'TP2',
        'tp3_count': 'TP3', 
        'tp4_count': 'TP4',
        'sl_count': 'SL',
        'avg_rr': 'Avg RR',
        'performance_score': 'Score'
    }
    
    available_columns = {k: v for k, v in columns_to_show.items() if k in display_df.columns}
    display_df = display_df[list(available_columns.keys())].rename(columns=available_columns)
    
    # Format numeric columns
    if 'Win Rate (%)' in display_df.columns:
        display_df['Win Rate (%)'] = display_df['Win Rate (%)'].round(1)
    if 'Avg RR' in display_df.columns:
        display_df['Avg RR'] = display_df['Avg RR'].round(2)
    if 'Score' in display_df.columns:
        display_df['Score'] = display_df['Score'].round(1)
    
    # Display with styling
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Export functionality
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv_data = display_df.to_csv(index=False)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"top_performers_{timestamp}.csv",
            mime="text/csv"
        )
    
    with col2:
        json_data = display_df.to_json(orient='records')
        
        st.download_button(
            label="📋 Download JSON", 
            data=json_data,
            file_name=f"top_performers_{timestamp}.json",
            mime="application/json"
        )

def main():
    """Main function"""
    # Render header
    render_page_header()
    
    # Render filters
    filters = render_performance_filters()
    
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
        
        # Calculate comprehensive metrics
        with st.spinner("📊 Calculating performance metrics..."):
            metrics_df = calculate_comprehensive_metrics(processed_data, filters)
        
        if metrics_df.empty:
            st.warning("⚠️ No pairs meet the minimum criteria")
            st.info("Try reducing the minimum trades requirement in the sidebar")
            return
        
        # Render analysis sections
        st.markdown("---")
        top_performers = render_top_performers_overview(metrics_df, filters)
        
        st.markdown("---")
        render_performance_charts(top_performers, filters)
        
        st.markdown("---")
        render_detailed_table(top_performers)
        
        # Additional insights
        with st.expander("💡 Performance Insights & Analysis"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 Key Insights:**")
                avg_wr = top_performers['win_rate'].mean()
                if avg_wr >= 65:
                    st.success(f"🔥 Excellent overall performance: {avg_wr:.1f}% average win rate!")
                elif avg_wr >= 55:
                    st.info(f"👍 Good performance: {avg_wr:.1f}% average win rate.")
                else:
                    st.warning(f"⚠️ Performance needs improvement: {avg_wr:.1f}% average win rate.")
                
                # RR insights
                avg_rr = top_performers['avg_rr'].mean()
                if avg_rr >= 2.5:
                    st.success(f"🚀 Excellent risk management: {avg_rr:.2f} average RR!")
                elif avg_rr >= 2:
                    st.info(f"📈 Good risk management: {avg_rr:.2f} average RR.")
                else:
                    st.warning(f"📉 Risk management could improve: {avg_rr:.2f} average RR.")
            
            with col2:
                st.markdown("**📊 Portfolio Recommendations:**")
                
                # Recommend best balanced performers
                balanced_performers = top_performers[
                    (top_performers['win_rate'] >= 60) & 
                    (top_performers['avg_rr'] >= 2) &
                    (top_performers['total_signals'] >= 10)
                ]
                
                if not balanced_performers.empty:
                    st.success(f"🎯 {len(balanced_performers)} pairs show excellent balance")
                    st.markdown("**Top Balanced Picks:**")
                    for _, row in balanced_performers.head(3).iterrows():
                        st.write(f"• **{row['pair']}**: {row['win_rate']:.1f}% WR, {row['avg_rr']:.2f} RR")
                else:
                    st.info("Consider focusing on pairs with both good win rates and risk management")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
"""
Fixed modern metrics display components with proper time range support and error handling
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

def render_winrate_trend(data, filters=None):
    """
    Render winrate trend as the main focus with proper time range support
    """
    st.markdown("## 📈 Win Rate Trend Analysis")
    
    # Get filters with defaults
    time_range = filters.get('time_range', 'all') if filters else 'all'
    chart_period = filters.get('chart_period', 'Daily') if filters else 'Daily'
    show_ma = filters.get('show_moving_average', True) if filters else True
    
    # Map chart period to period code
    period_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M'}
    period_code = period_map.get(chart_period, 'D')
    
    # Show current settings
    col1, col2 = st.columns(2)
    with col1:
        try:
            from data_processing.winrate_calculator import get_time_range_label
            st.info(f"📅 **Time Range:** {get_time_range_label(time_range)}")
        except:
            st.info(f"📅 **Time Range:** {time_range}")
    with col2:
        st.info(f"📊 **Chart Period:** {chart_period}")
    
    # Debug information (can be commented out in production)
    with st.expander("🔍 Debug Info", expanded=False):
        debug_chart_data(data, time_range)
    
    # Try enhanced calculation with proper error handling
    try:
        from data_processing.winrate_calculator import calculate_period_winrates
        
        # Calculate winrates with better error handling
        winrate_data = calculate_period_winrates(data, period=period_code, time_range=time_range)
        
        if winrate_data is not None and not winrate_data.empty:
            st.success(f"✅ Chart data calculated: {len(winrate_data)} periods")
            render_enhanced_winrate_chart(winrate_data, show_ma, chart_period)
            render_trend_summary(winrate_data, time_range)
            return
        else:
            st.warning("⚠️ No winrate data calculated - trying fallback")
            
    except Exception as e:
        st.error(f"❌ Enhanced calculation failed: {e}")
        st.info("Falling back to basic calculation...")
    
    # Fallback to basic calculation
    render_basic_winrate_fallback(data, time_range)

def debug_chart_data(data, time_range):
    """Debug function to show data information"""
    if data is None or data.empty:
        st.write("❌ **No data available**")
        return
    
    st.write(f"**Total Records:** {len(data)}")
    
    if 'created_at' in data.columns:
        valid_dates = data['created_at'].notna().sum()
        st.write(f"**Valid Dates:** {valid_dates}")
        if valid_dates > 0:
            st.write(f"**Date Range:** {data['created_at'].min()} to {data['created_at'].max()}")
    
    if 'final_outcome' in data.columns:
        closed_trades = data['final_outcome'].notna().sum()
        outcomes = data['final_outcome'].value_counts()
        st.write(f"**Closed Trades:** {closed_trades}")
        st.write(f"**Outcomes:** {outcomes.to_dict()}")
    
    st.write(f"**Active Time Range:** {time_range}")

def render_enhanced_winrate_chart(winrate_data, show_ma=True, chart_period="Daily"):
    """Render enhanced winrate chart with comprehensive error handling"""
    try:
        if winrate_data is None or winrate_data.empty:
            st.warning("No chart data available")
            return
        
        # Validate required columns
        required_cols = ['period_date', 'winrate', 'total_trades']
        missing_cols = [col for col in required_cols if col not in winrate_data.columns]
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            return
        
        # Create the main chart
        fig = go.Figure()
        
        # Add main winrate line with proper data validation
        valid_data = winrate_data[
            winrate_data['winrate'].notna() & 
            winrate_data['period_date'].notna() &
            winrate_data['total_trades'].notna()
        ].copy()
        
        if valid_data.empty:
            st.warning("No valid data points for chart")
            return
        
        # Main winrate trace
        fig.add_trace(go.Scatter(
            x=valid_data['period_date'],
            y=valid_data['winrate'],
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
            fillcolor='rgba(0, 212, 106, 0.1)',
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>',
            customdata=valid_data['total_trades']
        ))
        
        # Add 50% reference line
        fig.add_hline(
            y=50,
            line_dash="dash",
            line_color=COLORS['text_muted'],
            opacity=0.5,
            annotation_text="Break Even (50%)"
        )
        
        # Add moving average if enabled and enough data
        if show_ma and len(valid_data) > 3:
            try:
                ma_window = min(7, max(3, len(valid_data) // 4))
                valid_data['ma'] = valid_data['winrate'].rolling(ma_window, min_periods=2).mean()
                
                if valid_data['ma'].notna().any():
                    fig.add_trace(go.Scatter(
                        x=valid_data['period_date'],
                        y=valid_data['ma'],
                        mode='lines',
                        name=f'{ma_window}-Period MA',
                        line=dict(
                            color=COLORS['yellow'],
                            width=2,
                            dash='dot'
                        ),
                        opacity=0.7,
                        hovertemplate='<b>%{x}</b><br>MA: %{y:.1f}%<extra></extra>'
                    ))
            except Exception as ma_error:
                st.warning(f"Moving average calculation failed: {ma_error}")
        
        # Update layout with responsive design
        fig.update_layout(
            title=f"Win Rate Trend - {chart_period} View",
            xaxis_title="Date",
            yaxis_title="Win Rate (%)",
            height=400,
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
                range=[0, max(100, valid_data['winrate'].max() + 10)],
                gridcolor="#2D3139",
                linecolor="#2D3139",
                tickfont=dict(color="#A0A0A0")
            )
        )
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Show data quality info
        st.success(f"📊 Chart rendered successfully with {len(valid_data)} data points")
        
    except Exception as e:
        st.error(f"Chart rendering failed: {e}")
        st.code(f"Error details: {str(e)}")

def render_basic_winrate_fallback(data, time_range='all'):
    """Basic winrate chart fallback with enhanced error handling"""
    st.warning("⚠️ Using basic chart (enhanced calculation failed)")
    
    try:
        if data is None or data.empty:
            st.error("No data available")
            return
        
        # Check required columns
        if 'created_at' not in data.columns or 'final_outcome' not in data.columns:
            st.error("Missing required columns (created_at or final_outcome)")
            return
        
        # Filter closed trades only
        closed_data = data[
            data['final_outcome'].notna() & 
            (data['final_outcome'] != 'open') &
            (data['final_outcome'] != '')
        ].copy()
        
        if closed_data.empty:
            st.warning("No closed trades found")
            return
        
        # Apply basic time filtering
        if time_range != 'all':
            closed_data = apply_basic_time_filter(closed_data, time_range)
            
            if closed_data.empty:
                st.warning(f"No data in {time_range} time range")
                return
        
        # Safe datetime conversion
        try:
            closed_data['created_at'] = pd.to_datetime(closed_data['created_at'], errors='coerce')
            closed_data = closed_data[closed_data['created_at'].notna()]
            
            # Remove timezone to prevent issues
            if closed_data['created_at'].dt.tz is not None:
                closed_data['created_at'] = closed_data['created_at'].dt.tz_localize(None)
        except Exception as dt_error:
            st.error(f"Datetime conversion failed: {dt_error}")
            return
        
        # Calculate daily stats
        closed_data['date'] = closed_data['created_at'].dt.date
        closed_data['is_winner'] = closed_data['final_outcome'].str.startswith('tp', na=False)
        
        daily_stats = closed_data.groupby('date').agg({
            'is_winner': ['sum', 'count']
        }).reset_index()
        
        daily_stats.columns = ['date', 'wins', 'total']
        daily_stats['winrate'] = (daily_stats['wins'] / daily_stats['total'] * 100).round(1)
        
        # Create basic chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['winrate'],
            mode='lines+markers',
            name='Win Rate',
            line=dict(color=COLORS['green'], width=3),
            marker=dict(size=6, color=COLORS['green']),
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>',
            customdata=daily_stats['total']
        ))
        
        fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=f"Basic Win Rate Trend ({time_range})",
            xaxis_title="Date",
            yaxis_title="Win Rate (%)",
            height=350,
            template="plotly_dark",
            paper_bgcolor="#1A1D24",
            plot_bgcolor="#1A1D24",
            font=dict(color="#FFFFFF")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Basic summary
        if not daily_stats.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Latest Win Rate", f"{daily_stats['winrate'].iloc[-1]:.1f}%")
            with col2:
                st.metric("Average Win Rate", f"{daily_stats['winrate'].mean():.1f}%")
            with col3:
                st.metric("Total Periods", f"{len(daily_stats)}")
        
    except Exception as e:
        st.error(f"Basic chart failed: {e}")
        st.code(f"Fallback error: {str(e)}")

def apply_basic_time_filter(df, time_range):
    """Apply basic time filtering"""
    try:
        now = pd.Timestamp.now()
        
        if time_range == '7d':
            cutoff = now - pd.Timedelta(days=7)
        elif time_range == '30d':
            cutoff = now - pd.Timedelta(days=30)
        elif time_range == 'mtd':
            cutoff = pd.Timestamp(now.year, now.month, 1)
        elif time_range == 'ytd':
            cutoff = pd.Timestamp(now.year, 1, 1)
        else:
            return df
        
        return df[df['created_at'] >= cutoff]
        
    except Exception as e:
        st.warning(f"Time filter error: {e}")
        return df

def render_trend_summary(winrate_data, time_range='all'):
    """Render trend summary with proper error handling"""
    if winrate_data is None or winrate_data.empty:
        return
        
    try:
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
        
        # Add trend analysis if enough data
        if len(winrate_data) > 2:
            try:
                from data_processing.winrate_calculator import calculate_winrate_trend
                trend_info = calculate_winrate_trend(winrate_data)
                
                if trend_info['trend'] != 'insufficient_data':
                    render_trend_indicator(trend_info)
            except Exception as trend_error:
                st.warning(f"Trend analysis failed: {trend_error}")
        
    except Exception as e:
        st.error(f"Trend summary failed: {e}")

def render_trend_indicator(trend_info):
    """Render trend direction indicator"""
    trend_icons = {
        'strongly_improving': '🚀',
        'improving': '📈',
        'stable': '📊',
        'declining': '📉',
        'strongly_declining': '🔻'
    }
    
    trend_colors = {
        'strongly_improving': COLORS['green'],
        'improving': COLORS['green'],
        'stable': COLORS['yellow'],
        'declining': COLORS['red'],
        'strongly_declining': COLORS['red']
    }
    
    trend_icon = trend_icons.get(trend_info['trend'], '📊')
    trend_color = trend_colors.get(trend_info['trend'], COLORS['yellow'])
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: 15px; padding: 10px; background-color: rgba(255,255,255,0.05); border-radius: 8px;">
        <p style="color: {trend_color}; font-size: 16px; margin: 0;">
            {trend_icon} <strong>{trend_info['trend'].replace('_', ' ').title()}</strong>
        </p>
        <p style="color: #A0A0A0; font-size: 12px; margin: 5px 0 0 0;">
            Slope: {trend_info['slope']:.3f}%/period
        </p>
    </div>
    """, unsafe_allow_html=True)

def get_winrate_color(winrate):
    """Get color based on winrate"""
    if winrate >= 60:
        return COLORS['green']
    elif winrate >= 40:
        return COLORS['yellow']
    else:
        return COLORS['red']

def render_summary_cards(data, filters=None):
    """Render summary metrics with proper time range support"""
    st.markdown("## 📊 Performance Overview")
    
    # Get time range for metrics calculation
    time_range = filters.get('time_range', 'all') if filters else 'all'
    
    # Calculate metrics with time range filter
    metrics = calculate_summary_metrics(data, time_range)
    
    # Create 4 columns for main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card(
            "Total Signals",
            f"{metrics['total_signals']:,}",
            f"📈 Active: {metrics['active_pairs']} pairs",
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
    

    
    # Show time range indicator
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import get_time_range_label
            st.info(f"📅 Metrics calculated for: **{get_time_range_label(time_range)}**")
        except:
            st.info(f"📅 Metrics calculated for: **{time_range}**")

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

def calculate_summary_metrics(data, time_range='all'):
    """Calculate summary metrics with proper time range filtering"""
    if data is None or data.empty:
        return get_empty_metrics()
    
    # Apply time range filter if not 'all'
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import apply_time_range_filter
            filtered_data = apply_time_range_filter(data, time_range, 'created_at')
        except Exception as e:
            st.warning(f"Time range filtering failed: {e}")
            filtered_data = data
    else:
        filtered_data = data
    
    if filtered_data is None or filtered_data.empty:
        return get_empty_metrics()
        
    metrics = {}
    
    try:
        # Basic counts
        metrics['total_signals'] = len(filtered_data)
        metrics['closed_trades'] = filtered_data['final_outcome'].notna().sum() if 'final_outcome' in filtered_data.columns else 0
        metrics['open_signals'] = metrics['total_signals'] - metrics['closed_trades']
        
        # Rates
        metrics['completion_rate'] = (metrics['closed_trades'] / metrics['total_signals'] * 100) if metrics['total_signals'] > 0 else 0
        metrics['open_rate'] = 100 - metrics['completion_rate']
        
        # Win/Loss metrics
        if 'final_outcome' in filtered_data.columns and metrics['closed_trades'] > 0:
            metrics['tp_hits'] = filtered_data['final_outcome'].str.startswith('tp', na=False).sum()
            metrics['sl_hits'] = (filtered_data['final_outcome'] == 'sl').sum()
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
        if 'rr_planned' in filtered_data.columns:
            rr_data = filtered_data['rr_planned'].dropna()
            metrics['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
        else:
            metrics['avg_rr'] = 0
        
        # Pair metrics
        if 'pair' in filtered_data.columns:
            metrics['active_pairs'] = filtered_data['pair'].nunique()
            metrics['top_pair'] = filtered_data['pair'].value_counts().index[0] if not filtered_data['pair'].empty else "N/A"
        else:
            metrics['active_pairs'] = 0
            metrics['top_pair'] = "N/A"
        
        # Today's signals (basic calculation)
        metrics['signals_today'] = 0
        if time_range == 'all' and 'created_at' in filtered_data.columns:
            try:
                today = pd.Timestamp.now().date()
                filtered_data_copy = filtered_data.copy()
                filtered_data_copy['created_date'] = pd.to_datetime(filtered_data_copy['created_at'], errors='coerce').dt.date
                metrics['signals_today'] = (filtered_data_copy['created_date'] == today).sum()
            except:
                metrics['signals_today'] = 0
        
    except Exception as e:
        st.error(f"Metrics calculation error: {e}")
        return get_empty_metrics()
    
    return metrics

def get_empty_metrics():
    """Return empty metrics dictionary"""
    return {
        'total_signals': 0,
        'closed_trades': 0,
        'open_signals': 0,
        'completion_rate': 0,
        'open_rate': 0,
        'tp_hits': 0,
        'sl_hits': 0,
        'win_rate': 0,
        'tp_rate': 0,
        'sl_rate': 0,
        'avg_rr': 0,
        'active_pairs': 0,
        'top_pair': 'N/A',
        'signals_today': 0
    }

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
"""
Modern metrics display components for LuxQuant with Blue-Gold theme
Enhanced with proper time range support and comprehensive error handling
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# LuxQuant Blue-Gold Theme Colors
COLORS = {
    "background": "#0B1426",           # Deep blue background
    "card_bg": "#1A2332",             # Dark blue-gray cards
    "green": "#FFD700",               # Gold for positive values
    "red": "#EF4444",                 # Red for negative
    "yellow": "#FFD700",              # Gold/yellow
    "blue": "#3B82F6",                # Primary blue
    "purple": "#6366F1",              # Indigo purple
    "text_muted": "#94A3B8",          # Light blue-gray text
    # Theme specific colors
    "primary_gold": "#FFD700",        # Main gold accent
    "secondary_gold": "#FFA500",      # Orange gold
    "blue_primary": "#1E40AF",        # Primary blue
    "blue_accent": "#3B82F6",         # Lighter blue
    "blue_light": "#60A5FA",          # Light blue
    "success": "#FFD700",             # Gold for success
    "warning": "#F59E0B",             # Amber warning
    "error": "#EF4444",               # Red error
    "text_primary": "#F8FAFC",        # Nearly white text
    "text_secondary": "#CBD5E1",      # Light gray text
    "border": "#334155",              # Blue-gray borders
    "surface": "#1E293B"              # Surface color
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
    
    # Show current settings with blue-gold theme
    col1, col2 = st.columns(2)
    with col1:
        try:
            from data_processing.winrate_calculator import get_time_range_label
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1A2332 0%, #1E293B 100%);
                       border: 1px solid #3B82F6; border-radius: 6px; 
                       padding: 8px; margin: 10px 0; color: #60A5FA;">
                📅 <strong>Time Range:</strong> {get_time_range_label(time_range)}
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1A2332 0%, #1E293B 100%);
                       border: 1px solid #3B82F6; border-radius: 6px; 
                       padding: 8px; margin: 10px 0; color: #60A5FA;">
                📅 <strong>Time Range:</strong> {time_range}
            </div>
            """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1A2332 0%, #1E293B 100%);
                   border: 1px solid #FFD700; border-radius: 6px; 
                   padding: 8px; margin: 10px 0; color: #FFD700;">
            📊 <strong>Chart Period:</strong> {chart_period}
        </div>
        """, unsafe_allow_html=True)
    
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
    """Render enhanced winrate chart with blue-gold theme"""
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
        
        # Main winrate trace with gold color
        fig.add_trace(go.Scatter(
            x=valid_data['period_date'],
            y=valid_data['winrate'],
            mode='lines+markers',
            name='Win Rate',
            line=dict(
                color=COLORS['primary_gold'],
                width=3
            ),
            marker=dict(
                size=8,
                color=COLORS['primary_gold'],
                line=dict(color='white', width=1)
            ),
            fill='tonexty',
            fillcolor='rgba(255, 215, 0, 0.1)',
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
                            color=COLORS['blue_light'],
                            width=2,
                            dash='dot'
                        ),
                        opacity=0.7,
                        hovertemplate='<b>%{x}</b><br>MA: %{y:.1f}%<extra></extra>'
                    ))
            except Exception as ma_error:
                st.warning(f"Moving average calculation failed: {ma_error}")
        
        # Update layout with blue-gold theme
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
            paper_bgcolor=COLORS['card_bg'],
            plot_bgcolor=COLORS['card_bg'],
            font=dict(color=COLORS['text_primary'], family="Inter, sans-serif"),
            xaxis=dict(
                gridcolor=COLORS['border'],
                linecolor=COLORS['border'],
                tickfont=dict(color=COLORS['text_secondary'])
            ),
            yaxis=dict(
                range=[0, max(100, valid_data['winrate'].max() + 10)],
                gridcolor=COLORS['border'],
                linecolor=COLORS['border'],
                tickfont=dict(color=COLORS['text_secondary'])
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
    """Basic winrate chart fallback with blue-gold theme"""
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
        
        # Create basic chart with blue-gold theme
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['winrate'],
            mode='lines+markers',
            name='Win Rate',
            line=dict(color=COLORS['primary_gold'], width=3),
            marker=dict(size=6, color=COLORS['primary_gold']),
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>',
            customdata=daily_stats['total']
        ))
        
        fig.add_hline(y=50, line_dash="dash", line_color=COLORS['text_muted'], opacity=0.5)
        
        fig.update_layout(
            title=f"Basic Win Rate Trend ({time_range})",
            xaxis_title="Date",
            yaxis_title="Win Rate (%)",
            height=350,
            template="plotly_dark",
            paper_bgcolor=COLORS['card_bg'],
            plot_bgcolor=COLORS['card_bg'],
            font=dict(color=COLORS['text_primary'])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Basic summary with themed cards
        if not daily_stats.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                render_mini_metric_card("Latest Win Rate", f"{daily_stats['winrate'].iloc[-1]:.1f}%", COLORS['primary_gold'])
            with col2:
                render_mini_metric_card("Average Win Rate", f"{daily_stats['winrate'].mean():.1f}%", COLORS['blue_accent'])
            with col3:
                render_mini_metric_card("Total Periods", f"{len(daily_stats)}", COLORS['purple'])
        
    except Exception as e:
        st.error(f"Basic chart failed: {e}")
        st.code(f"Fallback error: {str(e)}")

def render_mini_metric_card(label, value, color):
    """Render small metric card"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
               border: 1px solid {COLORS['border']}; border-radius: 8px; 
               padding: 12px; text-align: center;">
        <p style="color: {COLORS['text_secondary']}; font-size: 11px; margin: 0; text-transform: uppercase;">
            {label}
        </p>
        <p style="color: {color}; font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">
            {value}
        </p>
    </div>
    """, unsafe_allow_html=True)

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
    """Render trend summary with blue-gold theme"""
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
            <div style="text-align: center; background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
                       border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 15px;">
                <p style="color: {COLORS['text_muted']}; font-size: 11px; margin: 0;">CURRENT</p>
                <p style="color: {color}; font-size: 20px; font-weight: 700; margin: 5px 0 0 0;">{current_wr:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
                       border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 15px;">
                <p style="color: {COLORS['text_muted']}; font-size: 11px; margin: 0;">AVERAGE</p>
                <p style="color: {COLORS['blue_accent']}; font-size: 20px; font-weight: 700; margin: 5px 0 0 0;">{avg_wr:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
                       border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 15px;">
                <p style="color: {COLORS['text_muted']}; font-size: 11px; margin: 0;">PEAK</p>
                <p style="color: {COLORS['primary_gold']}; font-size: 20px; font-weight: 700; margin: 5px 0 0 0;">{max_wr:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="text-align: center; background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
                       border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 15px;">
                <p style="color: {COLORS['text_muted']}; font-size: 11px; margin: 0;">LOWEST</p>
                <p style="color: {COLORS['red']}; font-size: 20px; font-weight: 700; margin: 5px 0 0 0;">{min_wr:.1f}%</p>
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
    """Render trend direction indicator with blue-gold theme"""
    trend_icons = {
        'strongly_improving': '🚀',
        'improving': '📈',
        'stable': '📊',
        'declining': '📉',
        'strongly_declining': '🔻'
    }
    
    trend_colors = {
        'strongly_improving': COLORS['primary_gold'],
        'improving': COLORS['primary_gold'],
        'stable': COLORS['blue_accent'],
        'declining': COLORS['red'],
        'strongly_declining': COLORS['red']
    }
    
    trend_icon = trend_icons.get(trend_info['trend'], '📊')
    trend_color = trend_colors.get(trend_info['trend'], COLORS['blue_accent'])
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: 15px; padding: 12px; 
               background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
               border: 1px solid {COLORS['border']}; border-radius: 8px;">
        <p style="color: {trend_color}; font-size: 16px; margin: 0;">
            {trend_icon} <strong>{trend_info['trend'].replace('_', ' ').title()}</strong>
        </p>
        <p style="color: {COLORS['text_muted']}; font-size: 12px; margin: 5px 0 0 0;">
            Slope: {trend_info['slope']:.3f}%/period
        </p>
    </div>
    """, unsafe_allow_html=True)

def get_winrate_color(winrate):
    """Get color based on winrate"""
    if winrate >= 60:
        return COLORS['primary_gold']
    elif winrate >= 40:
        return COLORS['blue_accent']
    else:
        return COLORS['red']

def render_summary_cards(data, filters=None):
    """Render summary metrics with blue-gold theme"""
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
            COLORS['blue_accent']
        )
    
    with col2:
        render_metric_card(
            "Overall Win Rate",
            f"{metrics['win_rate']:.2f}%",
            get_winrate_delta(metrics['win_rate']),
            get_winrate_color(metrics['win_rate'])
        )
    
    with col3:
        render_metric_card(
            "Completion Rate",
            f"{metrics['completion_rate']:.2f}%",
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
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
                       border: 1px solid {COLORS['blue_accent']}; border-radius: 6px; 
                       padding: 10px; margin: 15px 0; color: {COLORS['blue_light']}; text-align: center;">
                📅 <strong>Metrics calculated for:</strong> {get_time_range_label(time_range)}
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
                       border: 1px solid {COLORS['blue_accent']}; border-radius: 6px; 
                       padding: 10px; margin: 15px 0; color: {COLORS['blue_light']}; text-align: center;">
                📅 <strong>Metrics calculated for:</strong> {time_range}
            </div>
            """, unsafe_allow_html=True)

def render_metric_card(label, value, delta, color):
    """Render individual metric card with blue-gold theme"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['card_bg']} 0%, {COLORS['surface']} 100%);
               border: 1px solid {COLORS['border']}; border-radius: 12px; 
               padding: 20px; text-align: center;
               box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(59, 130, 246, 0.1);
               backdrop-filter: blur(12px); transition: all 0.3s ease;">
        <p style="color: {COLORS['text_secondary']}; font-size: 12px; margin: 0; 
                  text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">
            {label}
        </p>
        <h2 style="color: {color}; margin: 8px 0; font-size: 28px; font-weight: 700;
                   text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);">
            {value}
        </h2>
        <p style="color: {COLORS['text_muted']}; font-size: 11px; margin: 0;">
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
        return COLORS['primary_gold']
    elif rr >= 2:
        return COLORS['blue_accent']
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

def render_rolling_winrate_chart(data, filters=None):
    """Render rolling winrate chart with blue-gold theme"""
    st.subheader("📈 Rolling Win Rate Analysis")
    
    if data is None or data.empty:
        st.warning("No data available for rolling analysis")
        return
    
    # Get time range filter
    time_range = filters.get('time_range', 'all') if filters else 'all'
    
    # Apply time range filter
    if time_range != 'all':
        try:
            from data_processing.winrate_calculator import apply_time_range_filter
            filtered_data = apply_time_range_filter(data, time_range, 'created_at')
        except ImportError:
            filtered_data = data
    else:
        filtered_data = data
    
    if filtered_data is None or filtered_data.empty:
        st.warning("No data available after filtering")
        return
    
    # Filter closed trades
    closed_data = filtered_data[
        filtered_data['final_outcome'].notna() & 
        (filtered_data['final_outcome'] != 'open')
    ].copy()
    
    if closed_data.empty:
        st.warning("No closed trades for rolling analysis")
        return
    
    # Sort by date and calculate rolling metrics
    closed_data['created_at'] = pd.to_datetime(closed_data['created_at'], errors='coerce')
    closed_data = closed_data.sort_values('created_at').reset_index(drop=True)
    closed_data['is_winner'] = closed_data['final_outcome'].str.startswith('tp', na=False)
    
    # Calculate different rolling windows
    windows = [10, 30, 50]
    fig = go.Figure()
    
    for window in windows:
        if len(closed_data) >= window:
            closed_data[f'rolling_wr_{window}'] = closed_data['is_winner'].rolling(window=window, min_periods=5).mean() * 100
            
            # Color based on window size
            if window == 10:
                color = COLORS['primary_gold']
                dash = 'solid'
            elif window == 30:
                color = COLORS['blue_accent']
                dash = 'dash'
            else:
                color = COLORS['purple']
                dash = 'dot'
            
            fig.add_trace(go.Scatter(
                x=closed_data['created_at'],
                y=closed_data[f'rolling_wr_{window}'],
                mode='lines',
                name=f'{window}-Trade Rolling WR',
                line=dict(color=color, width=2, dash=dash),
                hovertemplate=f'<b>%{{x}}</b><br>{window}-Trade WR: %{{y:.1f}}%<extra></extra>'
            ))
    
    # Add 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color=COLORS['text_muted'], opacity=0.5)
    
    fig.update_layout(
        title="Rolling Win Rate Analysis",
        xaxis_title="Date",
        yaxis_title="Rolling Win Rate (%)",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        height=400,
        font=dict(color=COLORS['text_primary']),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            gridcolor=COLORS['border'],
            linecolor=COLORS['border'],
            tickfont=dict(color=COLORS['text_secondary'])
        ),
        yaxis=dict(
            gridcolor=COLORS['border'],
            linecolor=COLORS['border'],
            tickfont=dict(color=COLORS['text_secondary'])
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show rolling stats summary
    if len(closed_data) >= 30:
        col1, col2, col3 = st.columns(3)
        
        current_30_wr = closed_data['rolling_wr_30'].dropna().iloc[-1] if not closed_data['rolling_wr_30'].dropna().empty else 0
        
        with col1:
            render_mini_metric_card("Current 30-Trade WR", f"{current_30_wr:.1f}%", get_winrate_color(current_30_wr))
        
        with col2:
            avg_30_wr = closed_data['rolling_wr_30'].dropna().mean() if not closed_data['rolling_wr_30'].dropna().empty else 0
            render_mini_metric_card("Avg 30-Trade WR", f"{avg_30_wr:.1f}%", COLORS['blue_accent'])
        
        with col3:
            volatility = closed_data['rolling_wr_30'].dropna().std() if not closed_data['rolling_wr_30'].dropna().empty else 0
            render_mini_metric_card("Volatility", f"{volatility:.1f}%", COLORS['purple'])
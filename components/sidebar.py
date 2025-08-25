"""
Updated sidebar components for LuxQuant Analyzer with time range options
"""
import streamlit as st
from datetime import datetime, timedelta
from database.connection import get_connection_status

def render_sidebar():
    """Render sidebar and return filter values"""
    st.sidebar.title("LuxQuant Pro")
    st.sidebar.markdown("**Advanced Trading Signals Analytics**")
    
    # Connection status section
    render_connection_status()
    
    # Filters section  
    st.sidebar.markdown("---")
    st.sidebar.subheader("Time Range")
    
    filters = {}
    
    # Time range preset selector
    time_range = st.sidebar.selectbox(
        "Quick Select",
        ["All Time", "Year to Date", "Month to Date", "Last 30 Days", "Last 7 Days", "Custom Range"],
        help="Select predefined time ranges or custom"
    )
    
    # Calculate date ranges based on selection
    today = datetime.now().date()
    
    if time_range == "All Time":
        filters['date_from'] = None
        filters['date_to'] = None
        filters['time_range'] = "all"
        
    elif time_range == "Year to Date":
        filters['date_from'] = datetime(today.year, 1, 1).date()
        filters['date_to'] = today
        filters['time_range'] = "ytd"
        
    elif time_range == "Month to Date":
        filters['date_from'] = datetime(today.year, today.month, 1).date()
        filters['date_to'] = today
        filters['time_range'] = "mtd"
        
    elif time_range == "Last 30 Days":
        filters['date_from'] = today - timedelta(days=30)
        filters['date_to'] = today
        filters['time_range'] = "30d"
        
    elif time_range == "Last 7 Days":
        filters['date_from'] = today - timedelta(days=7)
        filters['date_to'] = today
        filters['time_range'] = "7d"
        
    elif time_range == "Custom Range":
        st.sidebar.markdown("**Custom Date Range**")
        filters['date_from'] = st.sidebar.date_input("From Date", value=None)
        filters['date_to'] = st.sidebar.date_input("To Date", value=None)
        filters['time_range'] = "custom"
    
    # Show selected range (read-only for non-custom)
    if time_range != "Custom Range":
        if filters['date_from'] and filters['date_to']:
            st.sidebar.info(f"📅 {filters['date_from']} to {filters['date_to']}")
        elif time_range == "All Time":
            st.sidebar.info("📅 All available data")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Additional Filters")
    
    # Pair filter - interactive
    filters['pair_filter'] = st.sidebar.text_input(
        "Trading Pairs", 
        placeholder="BTC, ETH, ADA",
        help="Enter pairs separated by commas"
    )
    
    # Analysis options
    st.sidebar.markdown("---")
    st.sidebar.subheader("Chart Options")
    
    filters['chart_period'] = st.sidebar.radio(
        "Win Rate Chart Period",
        ["Daily", "Weekly", "Monthly"],
        index=0,
        help="Granularity for win rate trend chart"
    )
    
    filters['show_moving_average'] = st.sidebar.checkbox(
        "Show Moving Average",
        value=True,
        help="Display 7-period moving average on charts"
    )
    
    # Auto-load flag
    filters['auto_load'] = True
    
    return filters

def render_connection_status():
    """Render database connection status section"""
    st.sidebar.subheader("Database Connection")
    
    try:
        connection_status = get_connection_status()
        
        if connection_status.get('connected'):
            st.sidebar.success("Connected & Auto-Loading")
            
            # Clear cache button only
            if st.sidebar.button("Clear Cache"):
                st.cache_data.clear()
                st.sidebar.success("Cache cleared!")
                st.rerun()
                
        else:
            st.sidebar.error("Connection Failed")
            error_msg = connection_status.get('error', 'Unknown error')
            
            if 'Missing PostgreSQL dependencies' in error_msg:
                st.sidebar.code("pip install psycopg2-binary")
            else:
                # Show the actual error message
                with st.sidebar.expander("Error Details"):
                    st.sidebar.text(error_msg)
                    
    except Exception as e:
        st.sidebar.error("Connection Check Failed")
        st.sidebar.text(f"Error: {str(e)}")

def render_filter_summary(filters):
    """Render applied filters summary"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Active Filters")
    
    active_filters = []
    
    # Time range summary
    time_range = filters.get('time_range', 'all')
    if time_range == 'all':
        active_filters.append("📅 All Time")
    elif time_range == 'ytd':
        active_filters.append("📅 Year to Date")
    elif time_range == 'mtd':
        active_filters.append("📅 Month to Date")
    elif time_range in ['30d', '7d']:
        days = time_range.replace('d', '')
        active_filters.append(f"📅 Last {days} Days")
    elif time_range == 'custom':
        if filters.get('date_from') and filters.get('date_to'):
            active_filters.append(f"📅 {filters['date_from']} to {filters['date_to']}")
    
    # Pair filter
    if filters.get('pair_filter', '').strip():
        pairs = filters['pair_filter'].replace(' ', '').upper()
        active_filters.append(f"💱 Pairs: {pairs}")
    
    # Chart options
    period = filters.get('chart_period', 'Daily')
    active_filters.append(f"📊 {period} Chart")
    
    if filters.get('show_moving_average'):
        active_filters.append("📈 Moving Average ON")
    
    # Display filters
    if active_filters:
        for filter_text in active_filters:
            st.sidebar.text(filter_text)
    else:
        st.sidebar.text("🔄 Default settings")
        
    # Show data count if available
    if 'data_count' in st.session_state:
        st.sidebar.metric("Filtered Signals", f"{st.session_state.data_count:,}")
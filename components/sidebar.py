"""
Sidebar components for LuxQuant Analyzer
"""
import streamlit as st
from database.connection import get_connection_status

def render_sidebar():
    """Render sidebar and return filter values"""
    st.sidebar.title("LuxQuant Pro")
    st.sidebar.markdown("**Advanced Trading Signals Analytics**")
    
    # Connection status section (display only, no buttons)
    render_connection_status()
    
    # Filters section  
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    
    filters = {}
    
    # Date filters
    filters['date_from'] = st.sidebar.date_input("From Date", value=None)
    filters['date_to'] = st.sidebar.date_input("To Date", value=None)
    
    # Pair filter - interactive
    filters['pair_filter'] = st.sidebar.text_input(
        "Pairs (comma-separated)", 
        placeholder="BTC, ETH, ADA",
        help="Enter pairs separated by commas. Changes apply instantly."
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
    
    if filters.get('date_from'):
        active_filters.append(f"📅 From: {filters['date_from']}")
    if filters.get('date_to'): 
        active_filters.append(f"📅 To: {filters['date_to']}")
    if filters.get('pair_filter', '').strip():
        pairs = filters['pair_filter'].replace(' ', '').upper()
        active_filters.append(f"💱 Pairs: {pairs}")
    
    if active_filters:
        for filter_text in active_filters:
            st.sidebar.text(filter_text)
    else:
        st.sidebar.text("🔄 No filters (showing all data)")
        
    # Show data count if available
    if 'data_count' in st.session_state:
        st.sidebar.metric("Filtered Signals", f"{st.session_state.data_count:,}")
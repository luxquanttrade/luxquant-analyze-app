"""
📊 Detailed Signal Data Page - LuxQuant Pro
Complete dataset view with filtering and export capabilities
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="📊 Detailed Signal Data - LuxQuant Pro",
    page_icon="📊",
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
        "background": "#0E1117"
    }

def render_page_header():
    """Render page header"""
    st.markdown("""
    <div style="margin-bottom: 30px;">
        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">
            📊 Detailed Call List by LuxQuant
        </h1>
        <p style="color: #A0A0A0; font-size: 16px; margin-top: 10px;">
            Complete dataset view with advanced filtering and export capabilities
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_data_filters():
    """Render advanced filtering sidebar"""
    st.sidebar.title("📊 Data Filters")
    
    filters = {}
    
    # Time Range Filter
    st.sidebar.subheader("📅 Time Range")
    time_range = st.sidebar.selectbox(
        "Quick Select",
        ["All Time", "Year to Date", "Month to Date", "Last 30 Days", "Last 7 Days", "Custom Range"],
        help="Select time range for data filtering"
    )
    
    # Map time range to internal format
    time_range_map = {
        "All Time": "all",
        "Year to Date": "ytd", 
        "Month to Date": "mtd",
        "Last 30 Days": "30d",
        "Last 7 Days": "7d",
        "Custom Range": "custom"
    }
    filters['time_range'] = time_range_map[time_range]
    
    # Custom date range
    if time_range == "Custom Range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            filters['date_from'] = st.date_input("From", value=None)
        with col2:
            filters['date_to'] = st.date_input("To", value=None)
    else:
        filters['date_from'] = None
        filters['date_to'] = None
    
    # Pair Filter
    st.sidebar.subheader("Trading Pairs")
    filters['pair_filter'] = st.sidebar.text_input(
        "Filter Pairs", 
        placeholder="BTC, ETH, ADA",
        help="Enter comma-separated pairs to filter"
    )
    
    # Outcome Filter
    st.sidebar.subheader("🎯 Outcomes")
    outcome_options = st.sidebar.multiselect(
        "Filter by Outcome",
        ["Open", "TP1", "TP2", "TP3", "TP4", "SL"],
        help="Filter signals by their outcomes"
    )
    filters['outcome_filter'] = outcome_options
    
    # RR Filter
    st.sidebar.subheader("⚖️ Risk-Reward Ratio")
    rr_range = st.sidebar.slider(
        "RR Range",
        min_value=0.0,
        max_value=10.0,
        value=(0.0, 10.0),
        step=0.1,
        help="Filter by planned RR ratio range"
    )
    filters['rr_min'] = rr_range[0]
    filters['rr_max'] = rr_range[1]
    
    return filters

def apply_advanced_filters(data, filters):
    """Apply advanced filtering beyond basic time/pair filters"""
    if data is None or data.empty:
        return data
    
    filtered_data = data.copy()
    
    # Outcome filter
    if filters.get('outcome_filter'):
        outcome_mapping = {
            'Open': [None, 'open', ''],
            'TP1': ['tp1'],
            'TP2': ['tp2'], 
            'TP3': ['tp3'],
            'TP4': ['tp4'],
            'SL': ['sl']
        }
        
        allowed_outcomes = []
        for selected in filters['outcome_filter']:
            allowed_outcomes.extend(outcome_mapping.get(selected, []))
        
        if 'final_outcome' in filtered_data.columns:
            # Handle None/NaN values for Open signals
            mask = filtered_data['final_outcome'].isin(allowed_outcomes)
            if None in allowed_outcomes:
                mask |= filtered_data['final_outcome'].isna()
            filtered_data = filtered_data[mask]
    
    # RR filter
    if 'rr_planned' in filtered_data.columns:
        rr_data = filtered_data['rr_planned']
        rr_mask = (rr_data >= filters['rr_min']) & (rr_data <= filters['rr_max'])
        # Include NaN values if min is 0 (to show signals without RR data)
        if filters['rr_min'] == 0:
            rr_mask |= rr_data.isna()
        filtered_data = filtered_data[rr_mask]
    
    return filtered_data

def format_dataframe_for_display(df):
    """Format dataframe for better display"""
    if df is None or df.empty:
        return df
    
    display_df = df.copy()
    
    # Step 1: Select columns in the order we want them displayed (use ORIGINAL column names)
    column_order = [
        'pair', 'created_at',
        'final_outcome', 'tp_level',
        'rr_planned'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in column_order if col in display_df.columns]
    display_df = display_df[available_columns]
    
    # Step 2: Rename columns for better display
    column_rename_map = {
        'signal_id': 'Signal ID',
        'pair': 'Coin Pair', 
        'created_at': 'Called At',
        'entry': 'Entry Price',
        'target1': 'Target 1',
        'target2': 'Target 2', 
        'target3': 'Target 3',
        'target4': 'Target 4',
        'stop1': 'Stop Loss 1',
        'stop2': 'Stop Loss 2',
        'final_outcome': 'Result',
        'tp_level': 'TP Level',
        'rr_planned': 'RR Planned',
        'rr_realized': 'RR Realized'
    }
    
    # Apply column renaming
    display_df = display_df.rename(columns=column_rename_map)
    
    # Step 3: Format values using the NEW column names
    # Format numeric columns
    numeric_cols = ['Entry Price', 'Target 1', 'Target 2', 'Target 3', 'Target 4', 
                   'Stop Loss 1', 'Stop Loss 2', 'RR Planned', 'RR Realized']
    for col in numeric_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: f"{x:.4f}" if pd.notna(x) and x != 0 else "None"
            )
    
    # Format datetime using NEW column name
    # Format datetime using NEW column name
    if 'Called At' in display_df.columns:
        called_at_wib = pd.to_datetime(display_df['Called At']) + pd.Timedelta(hours=7)
        display_df['Called At'] = called_at_wib.dt.strftime('%Y-%m-%d %H:%M:%S')

    
    # Format outcome column using NEW column name
    if 'Result' in display_df.columns:
        display_df['Result'] = display_df['Result'].fillna('None')
    
    # Format tp_level using NEW column name
    if 'TP Level' in display_df.columns:
        display_df['TP Level'] = display_df['TP Level'].fillna('None')
    
    return display_df

def render_data_summary(data, filtered_data):
    """Render data summary cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_signals = len(filtered_data) if filtered_data is not None else 0
        st.metric(
            "📊 Total Signals",
            f"{total_signals:,}",
            help="Number of signals after filtering"
        )
    
    with col2:
        if filtered_data is not None and 'pair' in filtered_data.columns:
            unique_pairs = filtered_data['pair'].nunique()
        else:
            unique_pairs = 0
        st.metric(
            "💱 Unique Pairs", 
            f"{unique_pairs}",
            help="Number of unique trading pairs"
        )
    
    with col3:
        if filtered_data is not None and 'final_outcome' in filtered_data.columns:
            closed_trades = filtered_data['final_outcome'].notna().sum()
        else:
            closed_trades = 0
        st.metric(
            "✅ Closed Trades",
            f"{closed_trades:,}",
            help="Number of closed trades (with outcomes)"
        )
    
    with col4:
        if filtered_data is not None and 'rr_planned' in filtered_data.columns:
            avg_rr = filtered_data['rr_planned'].mean()
            avg_rr_str = f"{avg_rr:.2f}" if pd.notna(avg_rr) else "N/A"
        else:
            avg_rr_str = "N/A"
        st.metric(
            "⚖️ Avg RR Ratio",
            avg_rr_str,
            help="Average planned risk-reward ratio"
        )


def main():
    """Main function"""
    # Render header
    render_page_header()
    
    # Render filters
    filters = render_data_filters()
    
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
        
        # Apply basic filters (time range, pairs)
        with st.spinner("🔍 Applying filters..."):
            filtered_data = apply_filters(processed_data, filters)
            
            # Apply advanced filters
            filtered_data = apply_advanced_filters(filtered_data, filters)
        
        # Show summary
        st.markdown("---")
        render_data_summary(processed_data, filtered_data)
        
        st.markdown("---")
        
        if filtered_data is None or filtered_data.empty:
            st.warning("⚠️ No data matches the selected filters")
            return
        
        # Main data display
        st.subheader("Call List Trade by LuxQuant")
        
        # Format data for display
        display_df = format_dataframe_for_display(filtered_data)
        
        # Display with custom styling
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600,  # Set fixed height for better scrolling
        )
        
        
        # Additional info
        with st.expander("ℹ️ Data Information"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Column Descriptions:**")
                st.markdown("""
                - **Signal ID**: Unique identifier for each signal
                - **Coin Pair**: Trading pair (e.g., BTCUSDT)
                - **Called At**: Signal creation timestamp
                - **Entry Price**: Entry price level
                - **Target 1-4**: Take profit targets
                - **Stop Loss 1-2**: Stop loss levels
                """)
            
            with col2:
                st.markdown("**🎯 Outcome Codes:**")
                st.markdown("""
                - **tp1-tp4**: Hit respective take profit level
                - **sl**: Hit stop loss
                - **None**: Signal still open/pending
                """)
                
                st.markdown("**⚖️ RR Ratios:**")
                st.markdown("""
                - **RR Planned**: Planned risk-reward ratio
                - **RR Realized**: Actual achieved RR ratio
                """)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
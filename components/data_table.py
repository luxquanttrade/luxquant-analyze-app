"""
Data table and export components
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from config.settings import DISPLAY_SETTINGS

def render_data_section(data):
    """Render the detailed data section with table and export"""
    if data is None or data.empty:
        st.warning("No data available for detailed view")
        return
    
    st.markdown("---")
    
    # Expandable detailed data view
    with st.expander("📊 Detailed Signal Data", expanded=False):
        render_detailed_data_table(data)
        render_export_section(data)

def render_detailed_data_table(data):
    """Render the detailed data table"""
    st.subheader("Complete Dataset")
    
    # Prepare data for display
    display_df = prepare_display_data(data)
    
    if display_df.empty:
        st.info("No data to display")
        return
    
    # Display table with formatting
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Show data summary
    render_data_summary(display_df)

def prepare_display_data(data):
    """Prepare data for display in table"""
    # Select relevant columns for display
    display_cols = [
        "signal_id", "pair", "created_at", "entry", 
        "target1", "target2", "target3", "target4",
        "stop1", "stop2", "final_outcome", "tp_level", 
        "rr_planned", "rr_realized"
    ]
    
    # Get available columns
    available_cols = [col for col in display_cols if col in data.columns]
    display_df = data[available_cols].copy()
    
    # Format numeric columns
    numeric_cols = display_df.select_dtypes(include=[np.number]).columns
    decimal_places = DISPLAY_SETTINGS['decimal_places']
    
    for col in numeric_cols:
        if col not in ['tp_level']:  # Don't round integer columns
            display_df[col] = display_df[col].round(decimal_places)
    
    # Format datetime columns
    if 'created_at' in display_df.columns:
        display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Sort by created_at if available
    if 'created_at' in display_df.columns:
        display_df = display_df.sort_values('created_at', ascending=False)
    
    return display_df

def render_data_summary(display_df):
    """Render summary statistics about the displayed data"""
    st.markdown("### Data Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", f"{len(display_df):,}")
    
    with col2:
        st.metric("Total Columns", f"{len(display_df.columns)}")
    
    with col3:
        # Calculate completeness
        non_null_cells = display_df.count().sum()
        total_cells = len(display_df) * len(display_df.columns)
        completeness = (non_null_cells / total_cells * 100) if total_cells > 0 else 0
        st.metric("Data Completeness", f"{completeness:.1f}%")
    
    with col4:
        # Memory usage
        memory_mb = display_df.memory_usage(deep=True).sum() / 1024 / 1024
        st.metric("Memory Usage", f"{memory_mb:.2f} MB")

def render_export_section(data):
    """Render export options"""
    st.markdown("### Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    # Prepare export data
    export_df = prepare_export_data(data)
    
    with col1:
        # CSV Export
        csv_data = export_df.to_csv(index=False)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"luxquant_analysis_{timestamp}.csv",
            mime="text/csv",
            help="Download complete dataset as CSV"
        )
    
    with col2:
        # JSON Export
        json_data = export_df.to_json(orient='records', date_format='iso')
        
        st.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"luxquant_analysis_{timestamp}.json",
            mime="application/json",
            help="Download complete dataset as JSON"
        )
    
    with col3:
        # Excel export option (if needed)
        st.button(
            "📊 Export to Excel",
            help="Excel export requires additional setup",
            disabled=True
        )

def prepare_export_data(data):
    """Prepare data for export with all relevant columns"""
    export_df = data.copy()
    
    # Format datetime columns for export
    datetime_cols = export_df.select_dtypes(include=['datetime64']).columns
    for col in datetime_cols:
        export_df[col] = export_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Replace NaN values with empty strings for cleaner export
    export_df = export_df.fillna('')
    
    return export_df

def render_column_info(data):
    """Render information about columns in the dataset"""
    if data is None or data.empty:
        return
    
    st.markdown("### Column Information")
    
    # Create column info dataframe
    column_info = []
    
    for col in data.columns:
        info = {
            'Column': col,
            'Type': str(data[col].dtype),
            'Non-Null': f"{data[col].count():,}",
            'Null %': f"{(data[col].isna().sum() / len(data) * 100):.1f}%"
        }
        
        # Add unique values for categorical columns
        if data[col].dtype == 'object' or data[col].dtype.name == 'category':
            unique_count = data[col].nunique()
            info['Unique'] = f"{unique_count:,}"
        else:
            # Add basic stats for numeric columns
            if pd.api.types.is_numeric_dtype(data[col]):
                info['Min'] = f"{data[col].min():.2f}" if pd.notna(data[col].min()) else "N/A"
                info['Max'] = f"{data[col].max():.2f}" if pd.notna(data[col].max()) else "N/A"
        
        column_info.append(info)
    
    column_df = pd.DataFrame(column_info)
    st.dataframe(column_df, use_container_width=True, hide_index=True)

def render_filter_summary(data, filters):
    """Render summary of applied filters"""
    if not filters:
        return
    
    st.markdown("### Applied Filters")
    
    active_filters = []
    
    if filters.get('date_from'):
        active_filters.append(f"**From Date:** {filters['date_from']}")
    
    if filters.get('date_to'):
        active_filters.append(f"**To Date:** {filters['date_to']}")
    
    if filters.get('pair_filter'):
        active_filters.append(f"**Pairs:** {filters['pair_filter']}")
    
    if active_filters:
        for filter_text in active_filters:
            st.write(filter_text)
        
        # Show impact of filters
        if data is not None:
            st.write(f"**Filtered Results:** {len(data):,} signals")
    else:
        st.write("No filters applied")

def render_data_quality_checks(data):
    """Render data quality checks and warnings"""
    if data is None or data.empty:
        return
    
    st.markdown("### Data Quality")
    
    issues = []
    
    # Check for missing critical data
    if 'signal_id' in data.columns and data['signal_id'].isna().any():
        missing_ids = data['signal_id'].isna().sum()
        issues.append(f"⚠️ {missing_ids} signals missing signal_id")
    
    if 'pair' in data.columns:
        unknown_pairs = (data['pair'] == 'UNKNOWN').sum()
        if unknown_pairs > 0:
            issues.append(f"⚠️ {unknown_pairs} signals with unknown trading pairs")
    
    if 'created_at' in data.columns:
        invalid_dates = data['created_at'].isna().sum()
        if invalid_dates > 0:
            issues.append(f"⚠️ {invalid_dates} signals with invalid dates")
    
    # Check RR data
    if 'rr_planned' in data.columns:
        missing_rr = data['rr_planned'].isna().sum()
        if missing_rr > len(data) * 0.5:  # More than 50% missing
            issues.append(f"⚠️ {missing_rr} signals missing RR data ({missing_rr/len(data)*100:.1f}%)")
    
    # Display issues or success message
    if issues:
        st.warning("Data Quality Issues Found:")
        for issue in issues:
            st.write(issue)
    else:
        st.success("✅ No major data quality issues detected")
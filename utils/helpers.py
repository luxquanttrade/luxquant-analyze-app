"""
Utility helper functions
"""
import pandas as pd
import numpy as np
import streamlit as st

from config.settings import COLUMN_MAPPINGS

def safe_col(df, candidates, default=None):
    """Safely get column name from candidates"""
    if df is None:
        return default
    for c in candidates:
        if c in df.columns:
            return c
    return default

def ensure_datetime(df, col):
    """Convert column to datetime if possible"""
    if df is not None and col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def normalize_column_names(df, mappings=None):
    """Normalize column names based on mappings"""
    if df is None or mappings is None:
        return df
    
    df_copy = df.copy()
    
    for standard_name, possible_names in mappings.items():
        found_col = safe_col(df_copy, possible_names)
        if found_col and found_col != standard_name:
            df_copy = df_copy.rename(columns={found_col: standard_name})
    
    return df_copy

def apply_filters(data, filters):
    """Apply filters to the processed data"""
    if data is None or data.empty:
        return data
    
    filtered_data = data.copy()
    
    # Date filters - perbaiki handling datetime  
    date_col = safe_col(filtered_data, COLUMN_MAPPINGS["created_at"])
    if date_col and date_col in filtered_data.columns:
        # Ensure datetime column is properly converted
        filtered_data[date_col] = pd.to_datetime(filtered_data[date_col], errors='coerce', utc=True)
        
        # Apply date range filters (only for custom range)
        if filters.get('time_range') == 'custom':
            if filters.get('date_from'):
                try:
                    date_from = pd.to_datetime(filters['date_from'], utc=True)
                    filtered_data = filtered_data[filtered_data[date_col] >= date_from]
                except Exception as e:
                    st.warning(f"Date from filter error: {e}")
                    
            if filters.get('date_to'):
                try:
                    date_to = pd.to_datetime(filters['date_to'], utc=True) + pd.Timedelta(days=1)
                    filtered_data = filtered_data[filtered_data[date_col] < date_to]
                except Exception as e:
                    st.warning(f"Date to filter error: {e}")
        
        # For other time ranges, filtering is handled in the winrate calculator
    
    # Pair filter
    if filters.get('pair_filter', '').strip():
        pairs = [p.strip().upper() for p in filters['pair_filter'].split(",") if p.strip()]
        if 'pair' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data["pair"].str.upper().isin(pairs)
            ]
    
    # Store data count in session state for sidebar
    st.session_state.data_count = len(filtered_data)
    
    return filtered_data

def format_number(value, decimal_places=2):
    """Format number with proper decimal places"""
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimal_places}f}"

def format_percentage(value, decimal_places=1):
    """Format value as percentage"""
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimal_places}f}%"

def calculate_basic_stats(df):
    """Calculate basic statistics for the dataset"""
    if df is None or df.empty:
        return {}
    
    stats = {
        'total_signals': len(df),
        'unique_pairs': df['pair'].nunique() if 'pair' in df.columns else 0,
    }
    
    # Date range
    date_col = safe_col(df, COLUMN_MAPPINGS["created_at"])
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        stats['date_range'] = {
            'start': df[date_col].min(),
            'end': df[date_col].max()
        }
    
    return stats

def clean_data(df):
    """Basic data cleaning"""
    if df is None:
        return df
    
    # Remove completely empty rows
    df_clean = df.dropna(how='all').copy()
    
    # Fill NaN values in essential columns
    essential_cols = ['pair', 'signal_id']
    for col in essential_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('UNKNOWN')
    
    return df_clean
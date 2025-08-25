"""
Complete utility helper functions with all required functions
"""
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

def normalize_column_names(df, mappings=None):
    """
    Normalize column names based on mappings
    
    Args:
        df: DataFrame to normalize
        mappings: Dict of {standard_name: [possible_names]}
        
    Returns:
        DataFrame with normalized column names
    """
    if df is None or mappings is None:
        return df
    
    df_copy = df.copy()
    
    for standard_name, possible_names in mappings.items():
        found_col = safe_col(df_copy, possible_names)
        if found_col and found_col != standard_name:
            df_copy = df_copy.rename(columns={found_col: standard_name})
    
    return df_copy

def safe_col(df, candidates, default=None):
    """Safely get column name from candidates"""
    if df is None or candidates is None:
        return default
    
    if isinstance(candidates, str):
        candidates = [candidates]
    
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    
    return default

def ensure_datetime(df, col):
    """Enhanced datetime conversion with error handling"""
    if df is None or col not in df.columns:
        return df
    
    try:
        # Try direct conversion first
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Remove timezone info if present
        if hasattr(df[col].dtype, 'tz') and df[col].dtype.tz is not None:
            df[col] = df[col].dt.tz_localize(None)
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ Datetime conversion failed for {col}: {e}")
        return df

def clean_data(df):
    """Enhanced data cleaning with better error handling"""
    if df is None or df.empty:
        return df
    
    try:
        df_clean = df.copy()
        
        # Remove completely empty rows
        initial_rows = len(df_clean)
        df_clean = df_clean.dropna(how='all')
        if len(df_clean) < initial_rows:
            st.info(f"🗑️ Removed {initial_rows - len(df_clean)} completely empty rows")
        
        # Clean essential string columns
        string_cols = ['pair', 'signal_id', 'final_outcome']
        for col in string_cols:
            if col in df_clean.columns:
                # Convert to string and clean
                df_clean[col] = df_clean[col].astype(str)
                
                # Replace common null representations
                null_values = ['nan', 'NaN', 'None', 'null', 'NULL', '']
                df_clean[col] = df_clean[col].replace(null_values, None)
                
                # Special handling for pair column
                if col == 'pair':
                    df_clean[col] = df_clean[col].fillna('UNKNOWN')
                    df_clean[col] = df_clean[col].str.upper().str.strip()
        
        # Clean numeric columns
        numeric_cols = ['entry', 'target1', 'target2', 'target3', 'target4', 'stop1', 'stop2', 'rr_planned']
        for col in numeric_cols:
            if col in df_clean.columns:
                # Convert to numeric
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
                # Remove unrealistic values
                if col in ['entry', 'target1', 'target2', 'target3', 'target4', 'stop1', 'stop2']:
                    # Remove negative or zero prices
                    df_clean.loc[df_clean[col] <= 0, col] = np.nan
                    # Remove extremely high prices (likely errors)
                    df_clean.loc[df_clean[col] > 1000000, col] = np.nan
        
        return df_clean
        
    except Exception as e:
        st.warning(f"⚠️ Data cleaning encountered issues: {e}")
        return df

def apply_filters(data, filters):
    """
    Enhanced filter application with better error handling and time range support
    """
    if data is None or data.empty:
        return data
    
    st.info(f"🔍 Applying filters to {len(data)} signals...")
    filtered_data = data.copy()
    
    try:
        # Time Range Filtering (this is the main fix)
        time_range = filters.get('time_range', 'all')
        
        if time_range != 'all' and 'created_at' in filtered_data.columns:
            st.info(f"⏰ Applying time range filter: {time_range}")
            filtered_data = apply_time_range_filter(filtered_data, time_range)
            st.info(f"📅 After time filter: {len(filtered_data)} signals")
        
        # Custom Date Range Filtering (for custom time range)
        if time_range == 'custom':
            if filters.get('date_from'):
                try:
                    date_from = pd.to_datetime(filters['date_from'])
                    before_count = len(filtered_data)
                    filtered_data = filtered_data[filtered_data['created_at'] >= date_from]
                    st.info(f"📅 Date FROM filter: {before_count} → {len(filtered_data)} signals")
                except Exception as e:
                    st.warning(f"⚠️ Date FROM filter error: {e}")
            
            if filters.get('date_to'):
                try:
                    date_to = pd.to_datetime(filters['date_to']) + pd.Timedelta(days=1)
                    before_count = len(filtered_data)
                    filtered_data = filtered_data[filtered_data['created_at'] < date_to]
                    st.info(f"📅 Date TO filter: {before_count} → {len(filtered_data)} signals")
                except Exception as e:
                    st.warning(f"⚠️ Date TO filter error: {e}")
        
        # Pair Filtering
        if filters.get('pair_filter', '').strip():
            pairs = [p.strip().upper() for p in filters['pair_filter'].split(",") if p.strip()]
            if 'pair' in filtered_data.columns and pairs:
                before_count = len(filtered_data)
                filtered_data = filtered_data[filtered_data["pair"].str.upper().isin(pairs)]
                st.info(f"💱 Pair filter ({', '.join(pairs)}): {before_count} → {len(filtered_data)} signals")
        
        # Store filtered count for sidebar display
        st.session_state.data_count = len(filtered_data)
        
        st.success(f"✅ Filtering complete: {len(filtered_data)} signals remaining")
        
        return filtered_data
        
    except Exception as e:
        st.error(f"❌ Filter application failed: {e}")
        return data

def apply_time_range_filter(df, time_range):
    """
    Apply time range filter with proper datetime handling
    """
    if df is None or df.empty or 'created_at' not in df.columns:
        return df
    
    try:
        # Ensure datetime column is properly formatted
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df['created_at']):
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # Remove timezone if present to prevent comparison errors
        if hasattr(df['created_at'].dtype, 'tz') and df['created_at'].dtype.tz is not None:
            df['created_at'] = df['created_at'].dt.tz_localize(None)
        
        # Calculate cutoff dates
        now = pd.Timestamp.now()
        
        if time_range == 'ytd':
            cutoff_date = pd.Timestamp(now.year, 1, 1)
            st.info(f"📅 Year to Date filter: from {cutoff_date.date()}")
            
        elif time_range == 'mtd':
            cutoff_date = pd.Timestamp(now.year, now.month, 1)
            st.info(f"📅 Month to Date filter: from {cutoff_date.date()}")
            
        elif time_range == '30d':
            cutoff_date = now - pd.Timedelta(days=30)
            st.info(f"📅 Last 30 Days filter: from {cutoff_date.date()}")
            
        elif time_range == '7d':
            cutoff_date = now - pd.Timedelta(days=7)
            st.info(f"📅 Last 7 Days filter: from {cutoff_date.date()}")
            
        else:
            return df  # No filtering for 'all' or unknown ranges
        
        # Apply the filter
        filtered_df = df[df['created_at'] >= cutoff_date]
        
        return filtered_df
        
    except Exception as e:
        st.error(f"❌ Time range filter failed: {e}")
        return df

def format_number(value, decimal_places=2):
    """Format number with proper decimal places"""
    if pd.isna(value) or value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimal_places}f}"
    except (ValueError, TypeError):
        return "N/A"

def format_percentage(value, decimal_places=1):
    """Format value as percentage"""
    if pd.isna(value) or value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "N/A"

def calculate_basic_stats(df):
    """Calculate comprehensive basic statistics"""
    if df is None or df.empty:
        return {
            'total_signals': 0,
            'unique_pairs': 0,
            'date_range': None,
            'completion_rate': 0,
            'avg_rr': 0
        }
    
    stats = {
        'total_signals': len(df),
        'unique_pairs': df['pair'].nunique() if 'pair' in df.columns else 0,
    }
    
    # Date range analysis
    if 'created_at' in df.columns and pd.api.types.is_datetime64_any_dtype(df['created_at']):
        valid_dates = df['created_at'].dropna()
        if not valid_dates.empty:
            stats['date_range'] = {
                'start': valid_dates.min(),
                'end': valid_dates.max(),
                'days': (valid_dates.max() - valid_dates.min()).days
            }
    
    # Outcome analysis
    if 'final_outcome' in df.columns:
        closed_trades = df['final_outcome'].notna().sum()
        stats['completion_rate'] = (closed_trades / len(df) * 100) if len(df) > 0 else 0
        
        if closed_trades > 0:
            tp_hits = df['final_outcome'].str.startswith('tp', na=False).sum()
            stats['win_rate'] = (tp_hits / closed_trades * 100)
        else:
            stats['win_rate'] = 0
    
    # RR analysis
    if 'rr_planned' in df.columns:
        rr_data = df['rr_planned'].dropna()
        stats['avg_rr'] = rr_data.mean() if len(rr_data) > 0 else 0
    
    return stats

def validate_data_quality(data):
    """Enhanced data quality validation"""
    if data is None or data.empty:
        return {"status": "empty", "issues": ["No data available"]}
    
    issues = []
    warnings = []
    
    # Check required columns
    required_cols = ['signal_id', 'pair', 'created_at']
    for col in required_cols:
        if col not in data.columns:
            issues.append(f"Missing required column: {col}")
        else:
            null_pct = (data[col].isna().sum() / len(data) * 100)
            if null_pct > 50:
                warnings.append(f"High null percentage in {col}: {null_pct:.1f}%")
    
    # Check datetime quality
    if 'created_at' in data.columns:
        if not pd.api.types.is_datetime64_any_dtype(data['created_at']):
            issues.append("created_at column is not datetime type")
        else:
            future_dates = (data['created_at'] > pd.Timestamp.now()).sum()
            if future_dates > 0:
                warnings.append(f"{future_dates} signals have future dates")
    
    # Check pair data
    if 'pair' in data.columns:
        unknown_pairs = (data['pair'] == 'UNKNOWN').sum()
        if unknown_pairs > len(data) * 0.5:
            warnings.append(f"High number of unknown pairs: {unknown_pairs}")
    
    # Check outcome data availability
    if 'final_outcome' in data.columns:
        closed_trades = data['final_outcome'].notna().sum()
        if closed_trades == 0:
            warnings.append("No closed trades found")
        else:
            completion_rate = (closed_trades / len(data) * 100)
            if completion_rate < 10:
                warnings.append(f"Low completion rate: {completion_rate:.1f}%")
    
    status = "good"
    if issues:
        status = "issues"
    elif warnings:
        status = "warnings"
    
    return {
        "status": status,
        "total_rows": len(data),
        "issues": issues,
        "warnings": warnings
    }

def get_data_summary(data, filters=None):
    """Get comprehensive data summary"""
    summary = {
        'total_records': len(data) if data is not None else 0,
        'data_quality': validate_data_quality(data),
        'basic_stats': calculate_basic_stats(data)
    }
    
    if filters:
        summary['applied_filters'] = {
            'time_range': filters.get('time_range', 'all'),
            'pair_filter': filters.get('pair_filter', ''),
            'chart_period': filters.get('chart_period', 'Daily')
        }
    
    return summary

def debug_data_issues(data):
    """Debug function to identify common data issues"""
    if data is None or data.empty:
        return {"error": "No data provided"}
    
    debug_info = {
        "shape": data.shape,
        "columns": data.columns.tolist(),
        "dtypes": data.dtypes.to_dict(),
        "null_counts": data.isnull().sum().to_dict(),
        "memory_usage": f"{data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
    }
    
    # Specific checks for common issues
    if 'created_at' in data.columns:
        debug_info["datetime_info"] = {
            "dtype": str(data['created_at'].dtype),
            "has_timezone": hasattr(data['created_at'].dtype, 'tz') and data['created_at'].dtype.tz is not None,
            "null_count": data['created_at'].isnull().sum(),
            "unique_count": data['created_at'].nunique()
        }
        
        if data['created_at'].notna().any():
            debug_info["datetime_info"]["min_date"] = str(data['created_at'].min())
            debug_info["datetime_info"]["max_date"] = str(data['created_at'].max())
    
    if 'final_outcome' in data.columns:
        debug_info["outcome_info"] = {
            "unique_outcomes": data['final_outcome'].unique().tolist(),
            "outcome_counts": data['final_outcome'].value_counts().to_dict()
        }
    
    return debug_info
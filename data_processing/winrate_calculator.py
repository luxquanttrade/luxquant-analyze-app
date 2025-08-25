"""
Enhanced winrate calculation with proper time range filtering and datetime handling
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def calculate_period_winrates(df, period='D', time_range='all'):
    """
    Calculate winrate per period with proper time range filtering
    
    Args:
        df: DataFrame with signals data
        period: 'D' for daily, 'W' for weekly, 'M' for monthly
        time_range: 'all', 'ytd', 'mtd', '30d', '7d', 'custom'
        
    Returns:
        DataFrame with period winrates
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        # Step 1: Ensure datetime column exists and is properly formatted
        date_col = 'created_at'
        if date_col not in df.columns:
            return pd.DataFrame()
        
        # Step 2: Clean and standardize datetime column
        df_clean = df.copy()
        df_clean = standardize_datetime_column(df_clean, date_col)
        
        # Step 3: Filter only closed trades (has outcome)
        closed_df = df_clean[
            df_clean['final_outcome'].notna() & 
            (df_clean['final_outcome'] != 'open') &
            (df_clean['final_outcome'] != '')
        ].copy()
        
        if closed_df.empty:
            return pd.DataFrame()
        
        # Step 4: Apply time range filtering BEFORE calculating winrates
        filtered_df = apply_time_range_filter(closed_df, time_range, date_col)
        
        if filtered_df.empty:
            return pd.DataFrame()
        
        # Step 5: Add win/loss flags
        filtered_df['is_winner'] = filtered_df['final_outcome'].str.startswith('tp', na=False)
        
        # Step 6: Calculate based on period
        if period == 'D':
            return calculate_daily_breakdown(filtered_df)
        elif period == 'W':
            return calculate_weekly_breakdown(filtered_df)
        elif period == 'M':
            return calculate_monthly_breakdown(filtered_df)
        else:
            return calculate_daily_breakdown(filtered_df)
            
    except Exception as e:
        st.error(f"Winrate calculation error: {e}")
        return pd.DataFrame()

def standardize_datetime_column(df, date_col):
    """
    Properly standardize datetime column to prevent comparison errors
    """
    try:
        # Convert to datetime with error handling
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', utc=True)
        
        # Remove timezone info to prevent comparison issues
        if df[date_col].dt.tz is not None:
            df[date_col] = df[date_col].dt.tz_localize(None)
        
        # Remove any NaT values
        df = df[df[date_col].notna()]
        
        return df
        
    except Exception as e:
        st.warning(f"Datetime standardization warning: {e}")
        return df

def apply_time_range_filter(df, time_range, date_col):
    """
    Apply time range filter to dataframe with proper datetime handling
    """
    if time_range == 'all':
        return df
    
    try:
        now = pd.Timestamp.now()
        
        if time_range == 'ytd':
            start_date = pd.Timestamp(now.year, 1, 1)
            return df[df[date_col] >= start_date]
            
        elif time_range == 'mtd':
            start_date = pd.Timestamp(now.year, now.month, 1)
            return df[df[date_col] >= start_date]
            
        elif time_range == '30d':
            start_date = now - pd.Timedelta(days=30)
            return df[df[date_col] >= start_date]
            
        elif time_range == '7d':
            start_date = now - pd.Timedelta(days=7)
            return df[df[date_col] >= start_date]
        
        return df
        
    except Exception as e:
        st.warning(f"Time filter error: {e}")
        return df

def calculate_daily_breakdown(df):
    """Calculate daily winrate breakdown with proper error handling"""
    try:
        # Group by day
        df['period_date'] = df['created_at'].dt.date
        
        daily_stats = df.groupby('period_date').agg({
            'signal_id': 'count',
            'is_winner': 'sum'
        }).reset_index()
        
        daily_stats.columns = ['period_date', 'total_trades', 'winning_trades']
        daily_stats['winrate'] = (daily_stats['winning_trades'] / daily_stats['total_trades'] * 100).round(2)
        
        # Convert period_date back to datetime for plotting
        daily_stats['period_date'] = pd.to_datetime(daily_stats['period_date'])
        
        # Ensure we have valid data
        daily_stats = daily_stats[daily_stats['total_trades'] > 0]
        
        return daily_stats
        
    except Exception as e:
        st.error(f"Daily breakdown calculation error: {e}")
        return pd.DataFrame()

def calculate_weekly_breakdown(df):
    """Calculate weekly winrate breakdown"""
    try:
        df['period'] = df['created_at'].dt.to_period('W')
        
        weekly_stats = df.groupby('period').agg({
            'signal_id': 'count',
            'is_winner': 'sum'
        }).reset_index()
        
        weekly_stats.columns = ['period', 'total_trades', 'winning_trades']
        weekly_stats['winrate'] = (weekly_stats['winning_trades'] / weekly_stats['total_trades'] * 100).round(2)
        weekly_stats['period_date'] = weekly_stats['period'].dt.start_time
        
        return weekly_stats[weekly_stats['total_trades'] > 0]
        
    except Exception as e:
        st.error(f"Weekly breakdown calculation error: {e}")
        return pd.DataFrame()

def calculate_monthly_breakdown(df):
    """Calculate monthly winrate breakdown"""
    try:
        df['period'] = df['created_at'].dt.to_period('M')
        
        monthly_stats = df.groupby('period').agg({
            'signal_id': 'count',
            'is_winner': 'sum'
        }).reset_index()
        
        monthly_stats.columns = ['period', 'total_trades', 'winning_trades']
        monthly_stats['winrate'] = (monthly_stats['winning_trades'] / monthly_stats['total_trades'] * 100).round(2)
        monthly_stats['period_date'] = monthly_stats['period'].dt.start_time
        
        return monthly_stats[monthly_stats['total_trades'] > 0]
        
    except Exception as e:
        st.error(f"Monthly breakdown calculation error: {e}")
        return pd.DataFrame()

def calculate_winrate_trend(winrate_data):
    """Calculate trend direction and slope with enhanced analysis"""
    if winrate_data is None or winrate_data.empty or len(winrate_data) < 2:
        return {'trend': 'insufficient_data', 'slope': 0}
    
    try:
        # Simple linear trend
        x = np.arange(len(winrate_data))
        y = winrate_data['winrate'].values
        
        # Remove any NaN values
        valid_mask = ~np.isnan(y)
        if valid_mask.sum() < 2:
            return {'trend': 'insufficient_data', 'slope': 0}
        
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        
        # Calculate slope
        slope = np.polyfit(x_valid, y_valid, 1)[0]
        
        # Determine trend with more granular thresholds
        if slope > 2:
            trend = 'strongly_improving'
        elif slope > 0.5:
            trend = 'improving'
        elif slope < -2:
            trend = 'strongly_declining'  
        elif slope < -0.5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Additional metrics
        recent_period = min(5, len(y_valid))
        recent_avg = np.mean(y_valid[-recent_period:]) if recent_period > 0 else 0
        overall_avg = np.mean(y_valid)
        
        return {
            'trend': trend,
            'slope': round(slope, 3),
            'current_winrate': y_valid[-1] if len(y_valid) > 0 else 0,
            'recent_avg_winrate': round(recent_avg, 2),
            'overall_avg_winrate': round(overall_avg, 2),
            'trend_strength': abs(slope)
        }
        
    except Exception as e:
        st.warning(f"Trend calculation error: {e}")
        return {'trend': 'insufficient_data', 'slope': 0}

def calculate_rolling_winrate(df, window=30, time_range='all'):
    """Calculate rolling winrate with proper time range filter"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        # Clean datetime first
        df_clean = standardize_datetime_column(df.copy(), 'created_at')
        
        # Apply time range filter
        filtered_df = apply_time_range_filter(df_clean, time_range, 'created_at')
        closed_df = filtered_df[
            filtered_df['final_outcome'].notna() & 
            (filtered_df['final_outcome'] != 'open')
        ].copy()
        
        if closed_df.empty:
            return pd.DataFrame()
        
        # Sort by date
        closed_df = closed_df.sort_values('created_at')
        closed_df['is_winner'] = closed_df['final_outcome'].str.startswith('tp', na=False)
        
        # Calculate rolling winrate
        closed_df['rolling_winrate'] = (
            closed_df['is_winner']
            .rolling(window=window, min_periods=1)
            .mean() * 100
        )
        
        return closed_df[['created_at', 'rolling_winrate', 'is_winner']].copy()
        
    except Exception as e:
        st.error(f"Rolling winrate calculation error: {e}")
        return pd.DataFrame()

def get_time_range_label(time_range):
    """Get human readable label for time range"""
    labels = {
        'all': 'All Time',
        'ytd': 'Year to Date',
        'mtd': 'Month to Date',
        '30d': 'Last 30 Days',
        '7d': 'Last 7 Days',
        'custom': 'Custom Range'
    }
    return labels.get(time_range, 'Unknown')

def get_period_label(period):
    """Get human readable label for chart period"""
    labels = {
        'D': 'Daily',
        'W': 'Weekly', 
        'M': 'Monthly'
    }
    return labels.get(period, 'Daily')

def debug_datetime_issues(df):
    """Debug function to identify datetime issues"""
    if df is None or df.empty:
        return {"error": "No data provided"}
    
    debug_info = {
        "total_rows": len(df),
        "datetime_column_exists": 'created_at' in df.columns,
        "datetime_info": {},
        "outcome_info": {}
    }
    
    if 'created_at' in df.columns:
        debug_info["datetime_info"] = {
            "dtype": str(df['created_at'].dtype),
            "null_count": df['created_at'].isna().sum(),
            "min_date": str(df['created_at'].min()) if df['created_at'].notna().any() else "No valid dates",
            "max_date": str(df['created_at'].max()) if df['created_at'].notna().any() else "No valid dates"
        }
    
    if 'final_outcome' in df.columns:
        debug_info["outcome_info"] = {
            "unique_outcomes": df['final_outcome'].unique().tolist(),
            "outcome_counts": df['final_outcome'].value_counts().to_dict(),
            "null_outcomes": df['final_outcome'].isna().sum()
        }
    
    return debug_info
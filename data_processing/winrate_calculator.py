"""
Enhanced winrate calculation with multiple time period support
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_period_winrates(df, period='D', time_range='all'):
    """
    Calculate winrate per period with flexible time ranges
    
    Args:
        df: DataFrame with signals data
        period: 'D' for daily, 'W' for weekly, 'M' for monthly
        time_range: 'all', 'ytd', 'mtd', '30d', '7d', 'custom'
        
    Returns:
        DataFrame with period winrates
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Ensure we have datetime column
    date_col = 'created_at'
    if date_col not in df.columns:
        return pd.DataFrame()
    
    # Filter only closed trades (has outcome)
    closed_df = df[df['final_outcome'].notna() & (df['final_outcome'] != 'open')].copy()
    
    if closed_df.empty:
        return pd.DataFrame()
    
    # Add win/loss flags
    closed_df['is_winner'] = closed_df['final_outcome'].str.startswith('tp', na=False)
    
    # Apply time range filtering based on created_at
    closed_df = apply_time_range_filter(closed_df, time_range, date_col)
    
    if closed_df.empty:
        return pd.DataFrame()
    
    # Calculate based on period
    if period == 'D':
        return calculate_daily_breakdown(closed_df)
    elif period == 'W':
        return calculate_weekly_breakdown(closed_df)
    elif period == 'M':
        return calculate_monthly_breakdown(closed_df)
    else:
        return calculate_daily_breakdown(closed_df)

def apply_time_range_filter(df, time_range, date_col):
    """Apply time range filter to dataframe"""
    if time_range == 'all':
        return df
    
    now = datetime.now()
    
    if time_range == 'ytd':
        start_date = datetime(now.year, 1, 1)
        return df[df[date_col] >= start_date]
        
    elif time_range == 'mtd':
        start_date = datetime(now.year, now.month, 1)
        return df[df[date_col] >= start_date]
        
    elif time_range == '30d':
        start_date = now - timedelta(days=30)
        return df[df[date_col] >= start_date]
        
    elif time_range == '7d':
        start_date = now - timedelta(days=7)
        return df[df[date_col] >= start_date]
    
    return df

def calculate_daily_breakdown(df):
    """Calculate daily winrate breakdown"""
    # Group by day
    df['period'] = df['created_at'].dt.date
    
    daily_stats = df.groupby('period').agg({
        'signal_id': 'count',
        'is_winner': 'sum'
    }).reset_index()
    
    daily_stats.columns = ['period', 'total_trades', 'winning_trades']
    daily_stats['winrate'] = (daily_stats['winning_trades'] / daily_stats['total_trades'] * 100).round(2)
    daily_stats['period_str'] = daily_stats['period'].astype(str)
    daily_stats['period_date'] = pd.to_datetime(daily_stats['period'])
    
    return daily_stats

def calculate_weekly_breakdown(df):
    """Calculate weekly winrate breakdown"""
    # Group by week
    df['period'] = df['created_at'].dt.to_period('W')
    
    weekly_stats = df.groupby('period').agg({
        'signal_id': 'count',
        'is_winner': 'sum'
    }).reset_index()
    
    weekly_stats.columns = ['period', 'total_trades', 'winning_trades']
    weekly_stats['winrate'] = (weekly_stats['winning_trades'] / weekly_stats['total_trades'] * 100).round(2)
    weekly_stats['period_str'] = weekly_stats['period'].astype(str)
    weekly_stats['period_date'] = weekly_stats['period'].dt.start_time
    
    return weekly_stats

def calculate_monthly_breakdown(df):
    """Calculate monthly winrate breakdown"""
    # Group by month
    df['period'] = df['created_at'].dt.to_period('M')
    
    monthly_stats = df.groupby('period').agg({
        'signal_id': 'count',
        'is_winner': 'sum'
    }).reset_index()
    
    monthly_stats.columns = ['period', 'total_trades', 'winning_trades']
    monthly_stats['winrate'] = (monthly_stats['winning_trades'] / monthly_stats['total_trades'] * 100).round(2)
    monthly_stats['period_str'] = monthly_stats['period'].astype(str)
    monthly_stats['period_date'] = monthly_stats['period'].dt.start_time
    
    return monthly_stats

def calculate_winrate_trend(winrate_data):
    """Calculate trend direction and slope with enhanced analysis"""
    if winrate_data.empty or len(winrate_data) < 2:
        return {'trend': 'insufficient_data', 'slope': 0}
    
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

def get_winrate_summary_stats(df, time_range='all'):
    """Get winrate summary statistics for specified time range"""
    if df is None or df.empty:
        return {}
    
    # Apply time range filter
    filtered_df = apply_time_range_filter(df, time_range, 'created_at')
    closed_df = filtered_df[filtered_df['final_outcome'].notna() & (filtered_df['final_outcome'] != 'open')].copy()
    
    if closed_df.empty:
        return {'error': 'No closed trades found in selected time range'}
    
    total_trades = len(closed_df)
    winning_trades = closed_df['final_outcome'].str.startswith('tp', na=False).sum()
    
    # TP level breakdown
    tp_breakdown = closed_df['final_outcome'].value_counts()
    
    stats = {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'overall_winrate': round((winning_trades / total_trades * 100), 2),
        'tp1_count': tp_breakdown.get('tp1', 0),
        'tp2_count': tp_breakdown.get('tp2', 0), 
        'tp3_count': tp_breakdown.get('tp3', 0),
        'tp4_count': tp_breakdown.get('tp4', 0),
        'sl_count': tp_breakdown.get('sl', 0),
        'time_range': time_range
    }
    
    return stats

def calculate_rolling_winrate(df, window=30, time_range='all'):
    """Calculate rolling winrate with time range filter"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Apply time range filter
    filtered_df = apply_time_range_filter(df, time_range, 'created_at')
    closed_df = filtered_df[filtered_df['final_outcome'].notna() & (filtered_df['final_outcome'] != 'open')].copy()
    
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
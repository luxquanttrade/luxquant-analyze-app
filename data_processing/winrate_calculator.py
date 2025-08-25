"""
Winrate calculation and trend analysis
"""
import pandas as pd
import numpy as np

def calculate_period_winrates(df, period='M'):
    """
    Calculate winrate per period with breakdown
    
    Args:
        df: DataFrame with signals data
        period: 'M' for monthly, 'D' for daily, 'A' for all time
        
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
    
    if period == 'A':  # All time - monthly breakdown
        return calculate_monthly_breakdown(closed_df)
    elif period == 'M':  # Monthly - daily breakdown  
        return calculate_daily_breakdown(closed_df)
    else:
        return pd.DataFrame()

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

def calculate_daily_breakdown(df, months_back=6):
    """Calculate daily winrate breakdown for recent months"""
    # Get recent data (last X months)
    cutoff_date = df['created_at'].max() - pd.DateOffset(months=months_back)
    recent_df = df[df['created_at'] >= cutoff_date].copy()
    
    if recent_df.empty:
        return pd.DataFrame()
    
    # Group by day
    recent_df['period'] = recent_df['created_at'].dt.date
    
    daily_stats = recent_df.groupby('period').agg({
        'signal_id': 'count',
        'is_winner': 'sum'
    }).reset_index()
    
    daily_stats.columns = ['period', 'total_trades', 'winning_trades']
    daily_stats['winrate'] = (daily_stats['winning_trades'] / daily_stats['total_trades'] * 100).round(2)
    daily_stats['period_str'] = daily_stats['period'].astype(str)
    daily_stats['period_date'] = pd.to_datetime(daily_stats['period'])
    
    return daily_stats

def calculate_winrate_trend(winrate_data):
    """Calculate trend direction and slope"""
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
    
    # Determine trend
    if slope > 1:
        trend = 'improving'
    elif slope < -1:
        trend = 'declining'  
    else:
        trend = 'stable'
    
    return {
        'trend': trend,
        'slope': round(slope, 3),
        'current_winrate': y_valid[-1] if len(y_valid) > 0 else 0,
        'avg_winrate': np.mean(y_valid)
    }

def get_winrate_summary_stats(df):
    """Get overall winrate summary statistics"""
    if df is None or df.empty:
        return {}
    
    closed_df = df[df['final_outcome'].notna() & (df['final_outcome'] != 'open')].copy()
    
    if closed_df.empty:
        return {'error': 'No closed trades found'}
    
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
        'sl_count': tp_breakdown.get('sl', 0)
    }
    
    return stats

def calculate_rolling_winrate(df, window=30):
    """Calculate rolling winrate over specified window"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    closed_df = df[df['final_outcome'].notna() & (df['final_outcome'] != 'open')].copy()
    
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
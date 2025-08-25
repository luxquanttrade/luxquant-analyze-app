"""
Comprehensive metrics calculation for trading signals
"""
import pandas as pd
import numpy as np

def compute_comprehensive_metrics(signals, outcomes=None):
    """
    Compute comprehensive signal metrics including RR ratios
    
    Args:
        signals: DataFrame with signal data
        outcomes: DataFrame with outcome data (optional)
        
    Returns:
        DataFrame with comprehensive metrics
    """
    if signals is None or signals.empty:
        return pd.DataFrame()

    df = signals.copy()
    
    # Ensure all required columns exist
    required_cols = ["signal_id", "pair", "entry", "target1", "target2", "target3", "target4", "stop1", "stop2"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    # Calculate risk-reward metrics
    df = calculate_rr_metrics(df)
    
    # Merge with outcomes if provided
    if outcomes is not None and not outcomes.empty:
        df = df.merge(outcomes, on="signal_id", how="left")
        df = calculate_performance_metrics(df)
    
    return df

def calculate_rr_metrics(df):
    """Calculate risk-reward ratios for all targets"""
    # Calculate stop loss used (prefer stop1, fallback to stop2)
    df["stop_used"] = np.where(df["stop1"].notna(), df["stop1"], df["stop2"])
    
    # Find highest available target
    df["highest_target"] = get_highest_target(df)
    
    # Calculate risk distance (entry to stop)
    entry_col = df["entry"]
    stop_col = df["stop_used"]
    df["risk_distance"] = np.abs(entry_col - stop_col)
    
    # Calculate individual target RR ratios
    for i in range(1, 5):
        target_col = f"target{i}"
        rr_col = f"rr_target{i}"
        
        if target_col in df.columns:
            reward_distance = np.abs(df[target_col] - entry_col)
            df[rr_col] = calculate_rr_ratio(reward_distance, df["risk_distance"])
    
    # Overall planned RR (using highest target)
    if "highest_target" in df.columns:
        reward_distance = np.abs(df["highest_target"] - entry_col)
        df["rr_planned"] = calculate_rr_ratio(reward_distance, df["risk_distance"])
    
    return df

def get_highest_target(df):
    """Find the highest available target for each signal"""
    highest_target = np.full(len(df), np.nan)
    
    # Check targets in descending order
    for target_col in ["target4", "target3", "target2", "target1"]:
        if target_col in df.columns:
            mask = df[target_col].notna() & pd.isna(highest_target)
            highest_target[mask] = df.loc[mask, target_col]
    
    return highest_target

def calculate_rr_ratio(reward_distance, risk_distance):
    """Calculate risk-reward ratio safely"""
    return np.where(
        (risk_distance > 0) & (risk_distance.notna()) & (reward_distance.notna()),
        reward_distance / risk_distance,
        np.nan
    )

def calculate_performance_metrics(df):
    """Calculate performance metrics when outcomes are available"""
    # Realized RR (actual RR achieved)
    df["rr_realized"] = calculate_realized_rr(df)
    
    # Performance flags
    df["is_winner"] = df["final_outcome"].str.startswith("tp", na=False)
    df["is_loser"] = df["final_outcome"] == "sl"
    df["is_open"] = df["final_outcome"].isna() | (df["final_outcome"] == "open")
    
    return df

def calculate_realized_rr(df):
    """Calculate the actual RR ratio achieved based on outcome"""
    realized_rr = np.full(len(df), np.nan)
    
    # For TP outcomes, use the corresponding target RR
    for i in range(1, 5):
        tp_mask = df["final_outcome"] == f"tp{i}"
        rr_col = f"rr_target{i}"
        
        if tp_mask.any() and rr_col in df.columns:
            realized_rr[tp_mask] = df.loc[tp_mask, rr_col]
    
    # For SL outcomes, RR = -1 (full loss)
    sl_mask = df["final_outcome"] == "sl"
    realized_rr[sl_mask] = -1.0
    
    return realized_rr

def calculate_portfolio_metrics(df):
    """Calculate portfolio-level metrics"""
    if df is None or df.empty:
        return {}
    
    metrics = {}
    
    # Basic counts
    metrics["total_signals"] = len(df)
    metrics["closed_trades"] = (~df["is_open"]).sum() if "is_open" in df.columns else 0
    metrics["open_signals"] = df["is_open"].sum() if "is_open" in df.columns else len(df)
    
    if "is_winner" in df.columns and "is_loser" in df.columns:
        metrics["tp_hits"] = df["is_winner"].sum()
        metrics["sl_hits"] = df["is_loser"].sum()
        
        # Win rate
        closed_trades = metrics["closed_trades"]
        if closed_trades > 0:
            metrics["win_rate"] = (metrics["tp_hits"] / closed_trades) * 100
        else:
            metrics["win_rate"] = 0
    
    # RR metrics
    if "rr_planned" in df.columns:
        rr_data = df["rr_planned"].dropna()
        if len(rr_data) > 0:
            metrics["avg_rr_planned"] = rr_data.mean()
            metrics["median_rr_planned"] = rr_data.median()
            metrics["min_rr_planned"] = rr_data.min()
            metrics["max_rr_planned"] = rr_data.max()
    
    if "rr_realized" in df.columns:
        rr_realized = df["rr_realized"].dropna()
        if len(rr_realized) > 0:
            metrics["avg_rr_realized"] = rr_realized.mean()
            metrics["total_realized_rr"] = rr_realized.sum()
    
    return metrics

def calculate_pair_metrics(df):
    """Calculate metrics by trading pair"""
    if df is None or df.empty or "pair" not in df.columns:
        return pd.DataFrame()
    
    # Group by pair and calculate metrics
    pair_groups = df.groupby("pair")
    
    pair_stats = []
    for pair, group in pair_groups:
        stats = calculate_portfolio_metrics(group)
        stats["pair"] = pair
        pair_stats.append(stats)
    
    pair_metrics = pd.DataFrame(pair_stats)
    
    # Sort by win rate (descending) and total signals
    if "win_rate" in pair_metrics.columns:
        pair_metrics = pair_metrics.sort_values(
            ["win_rate", "total_signals"], 
            ascending=[False, False]
        )
    
    return pair_metrics

def get_rr_distribution(df, bins=None):
    """Get risk-reward ratio distribution for analysis"""
    if df is None or "rr_planned" not in df.columns:
        return {}
    
    rr_data = df["rr_planned"].dropna()
    if len(rr_data) == 0:
        return {}
    
    if bins is None:
        bins = [0, 1, 2, 3, 4, 5, float('inf')]
    
    bin_labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]
    bin_labels[-1] = f"{bins[-2]}+"
    
    distribution = pd.cut(rr_data, bins=bins, labels=bin_labels, right=False).value_counts()
    
    return {
        "distribution": distribution.to_dict(),
        "total_signals": len(rr_data),
        "avg_rr": rr_data.mean(),
        "median_rr": rr_data.median()
    }
"""
Signal outcome inference from updates data
"""
import pandas as pd
import numpy as np
from config.settings import OUTCOME_RANKING, COLUMN_MAPPINGS
from utils.helpers import safe_col, ensure_datetime

def infer_outcome_from_updates(updates):
    """
    Infer final outcome from signal updates with comprehensive pattern matching
    
    Args:
        updates: DataFrame with signal updates
        
    Returns:
        DataFrame with columns: signal_id, final_outcome, tp_level
    """
    if updates is None or updates.empty:
        return pd.DataFrame(columns=["signal_id", "final_outcome", "tp_level"])

    upd = updates.copy()
    
    # Find and normalize time column
    upd = prepare_updates_data(upd)
    
    # Find update_type column
    type_col = safe_col(upd, COLUMN_MAPPINGS["update_type"])
    if type_col and type_col != "update_type":
        upd["update_type"] = upd[type_col]
        
    # Check required columns
    if "signal_id" not in upd.columns or "update_type" not in upd.columns:
        return pd.DataFrame(columns=["signal_id", "final_outcome", "tp_level"])

    # Normalize update types
    upd["update_type_norm"] = upd["update_type"].apply(normalize_update_type)
    
    # Calculate final outcomes
    final_outcomes = calculate_final_outcomes(upd)
    
    return final_outcomes

def prepare_updates_data(upd):
    """Prepare updates data for processing"""
    # Find time column and sort by it
    time_col = safe_col(upd, COLUMN_MAPPINGS["time"])
    if time_col:
        upd = ensure_datetime(upd, time_col)
        upd = upd.sort_values(["signal_id", time_col])
    
    return upd

def normalize_update_type(update_value):
    """
    Normalize update type with comprehensive pattern matching
    
    Args:
        update_value: Raw update type value
        
    Returns:
        Normalized update type (tp1, tp2, tp3, tp4, sl, or original)
    """
    if pd.isna(update_value):
        return None
    
    s = str(update_value).lower().strip()
    
    # TP patterns with priority (highest first)
    tp_patterns = [
        (["tp4", "target 4", "target4", "t4"], "tp4"),
        (["tp3", "target 3", "target3", "t3"], "tp3"),
        (["tp2", "target 2", "target2", "t2"], "tp2"),
        (["tp1", "target 1", "target1", "t1"], "tp1"),
    ]
    
    for patterns, result in tp_patterns:
        if any(pattern in s for pattern in patterns):
            return result
            
    # SL patterns
    sl_patterns = ["sl", "stop", "stop loss", "stoploss"]
    if any(pattern in s for pattern in sl_patterns):
        return "sl"
        
    # Check for "hit" patterns
    if "hit" in s:
        hit_patterns = [
            (["4", "tp4", "target 4"], "tp4"),
            (["3", "tp3", "target 3"], "tp3"),
            (["2", "tp2", "target 2"], "tp2"),
            (["1", "tp1", "target 1"], "tp1"),
        ]
        
        for patterns, result in hit_patterns:
            if any(pattern in s for pattern in patterns):
                return result
    
    # Check for "reached" patterns
    if "reached" in s:
        if any(x in s for x in ["4", "tp4"]):
            return "tp4"
        elif any(x in s for x in ["3", "tp3"]):
            return "tp3"
        elif any(x in s for x in ["2", "tp2"]):
            return "tp2"
        elif any(x in s for x in ["1", "tp1"]):
            return "tp1"
    
    return s

def calculate_final_outcomes(upd):
    """Calculate final outcomes for each signal"""
    # Ranking system based on outcome hierarchy
    upd["rank"] = upd["update_type_norm"].map(OUTCOME_RANKING)
    
    # Get max rank per signal (highest achievement)
    valid_updates = upd[upd["rank"].notna()]
    if valid_updates.empty:
        return pd.DataFrame(columns=["signal_id", "final_outcome", "tp_level"])
        
    # Group by signal and get maximum rank achieved
    agg = valid_updates.groupby("signal_id").agg(
        max_rank=("rank", "max")
    ).reset_index()
    
    agg["tp_level"] = agg["max_rank"].astype(int)
    
    # Map back to outcome names
    inv_rank = {v: k for k, v in OUTCOME_RANKING.items()}
    agg["final_outcome"] = agg["tp_level"].map(lambda r: inv_rank.get(r, "open"))
    agg = agg.drop(columns=["max_rank"])
    
    return agg

def get_outcome_statistics(outcomes):
    """Get statistics about outcomes"""
    if outcomes is None or outcomes.empty:
        return {}
    
    outcome_counts = outcomes["final_outcome"].value_counts()
    
    stats = {
        "total_outcomes": len(outcomes),
        "tp_hits": outcome_counts.filter(regex=r'^tp\d+').sum(),
        "sl_hits": outcome_counts.get("sl", 0),
        "outcome_distribution": outcome_counts.to_dict()
    }
    
    # Calculate win rate
    closed_trades = stats["tp_hits"] + stats["sl_hits"]
    stats["win_rate"] = (stats["tp_hits"] / closed_trades * 100) if closed_trades > 0 else 0
    
    return stats

def validate_outcomes(outcomes, signals=None):
    """Validate outcome inference results"""
    validation = {
        "is_valid": True,
        "warnings": [],
        "coverage": 0
    }
    
    if outcomes is None or outcomes.empty:
        validation["is_valid"] = False
        validation["warnings"].append("No outcomes inferred")
        return validation
    
    # Check coverage if signals provided
    if signals is not None and not signals.empty:
        total_signals = len(signals)
        signals_with_outcomes = len(outcomes)
        validation["coverage"] = (signals_with_outcomes / total_signals * 100) if total_signals > 0 else 0
        
        if validation["coverage"] < 50:
            validation["warnings"].append(f"Low outcome coverage: {validation['coverage']:.1f}%")
    
    # Check for invalid outcomes
    valid_outcomes = list(OUTCOME_RANKING.keys()) + ["open"]
    invalid_outcomes = outcomes[~outcomes["final_outcome"].isin(valid_outcomes)]
    if not invalid_outcomes.empty:
        validation["warnings"].append(f"{len(invalid_outcomes)} signals with invalid outcomes")
    
    return validation
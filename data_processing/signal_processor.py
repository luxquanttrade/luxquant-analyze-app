"""
Main signal processing pipeline
"""
import pandas as pd
import numpy as np
from config.settings import COLUMN_MAPPINGS, REQUIRED_SIGNAL_COLUMNS
from utils.helpers import safe_col, ensure_datetime, normalize_column_names, clean_data
from data_processing.outcome_inference import infer_outcome_from_updates
from data_processing.metrics_calculator import compute_comprehensive_metrics

def process_signals(raw_data):
    """
    Main signal processing pipeline
    
    Args:
        raw_data: Dictionary containing raw data from database
        
    Returns:
        Processed DataFrame with signals, outcomes, and metrics
    """
    if not raw_data or 'signals' not in raw_data:
        return pd.DataFrame()
    
    # Get raw datasets
    df_signals = raw_data.get('signals')
    df_updates = raw_data.get('updates')
    
    if df_signals is None or df_signals.empty:
        return pd.DataFrame()
    
    # Step 1: Clean and normalize signals data
    df_processed = prepare_signals_data(df_signals)
    
    # Step 2: Process outcomes from updates
    outcomes_df = process_signal_outcomes(df_updates)
    
    # Step 3: Calculate comprehensive metrics
    final_df = compute_comprehensive_metrics(df_processed, outcomes_df)
    
    return final_df

def prepare_signals_data(df_signals):
    """Prepare and normalize signals data"""
    df = clean_data(df_signals.copy())
    
    # Normalize column names
    df = normalize_column_names(df, COLUMN_MAPPINGS)
    
    # Ensure required columns exist
    for col in REQUIRED_SIGNAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    
    # Handle datetime columns
    created_col = safe_col(df, COLUMN_MAPPINGS["created_at"])
    if created_col:
        df = ensure_datetime(df, created_col)
        if created_col != "created_at":
            df = df.rename(columns={created_col: "created_at"})
    else:
        df["created_at"] = pd.NaT
    
    # Handle pair column
    pair_col = safe_col(df, COLUMN_MAPPINGS["pair"])
    if pair_col and pair_col != "pair":
        df = df.rename(columns={pair_col: "pair"})
    elif "pair" not in df.columns:
        df["pair"] = "UNKNOWN"
    
    # Ensure pair column is string and uppercase
    df["pair"] = df["pair"].astype(str).str.upper()
    
    return df

def process_signal_outcomes(df_updates):
    """Process signal outcomes from updates data"""
    if df_updates is None or df_updates.empty:
        return pd.DataFrame(columns=["signal_id", "final_outcome", "tp_level"])
    
    # Use the outcome inference logic
    outcomes = infer_outcome_from_updates(df_updates)
    
    return outcomes

def validate_processed_data(df):
    """Validate processed data quality"""
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': []
    }
    
    if df is None or df.empty:
        validation_results['is_valid'] = False
        validation_results['errors'].append("No data processed")
        return validation_results
    
    # Check required columns
    missing_cols = [col for col in ['signal_id', 'pair'] if col not in df.columns]
    if missing_cols:
        validation_results['warnings'].append(f"Missing columns: {missing_cols}")
    
    # Check data quality
    if 'pair' in df.columns:
        unknown_pairs = (df['pair'] == 'UNKNOWN').sum()
        if unknown_pairs > 0:
            validation_results['warnings'].append(f"{unknown_pairs} signals with unknown pairs")
    
    # Check datetime
    if 'created_at' in df.columns:
        invalid_dates = df['created_at'].isna().sum()
        if invalid_dates > 0:
            validation_results['warnings'].append(f"{invalid_dates} signals with invalid dates")
    
    return validation_results

def get_processing_summary(df):
    """Get summary of processing results"""
    if df is None or df.empty:
        return {"total_signals": 0}
    
    summary = {
        "total_signals": len(df),
        "unique_pairs": df['pair'].nunique() if 'pair' in df.columns else 0,
        "signals_with_outcomes": df['final_outcome'].notna().sum() if 'final_outcome' in df.columns else 0,
        "open_signals": len(df) - df['final_outcome'].notna().sum() if 'final_outcome' in df.columns else len(df)
    }
    
    # Date range
    if 'created_at' in df.columns and df['created_at'].notna().any():
        summary["date_range"] = {
            "start": df['created_at'].min(),
            "end": df['created_at'].max()
        }
    
    return summary
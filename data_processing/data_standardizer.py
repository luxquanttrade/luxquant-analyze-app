"""
Enhanced Data Standardization Module with better datetime handling
"""
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import streamlit as st

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_signals(raw_data):
    """
    Enhanced signal processing with better error handling and datetime standardization
    """
    if not raw_data or 'signals' not in raw_data:
        st.error("❌ No signals data found in raw data")
        return pd.DataFrame()
    
    # Get raw datasets
    df_signals = raw_data.get('signals')
    df_updates = raw_data.get('updates')
    
    if df_signals is None or df_signals.empty:
        st.error("❌ Signals dataframe is empty")
        return pd.DataFrame()
    
    st.info(f"📊 Processing {len(df_signals)} raw signals...")
    
    try:
        # Step 1: Standardize and clean signals data
        df_processed = standardize_signals_data(df_signals)
        
        if df_processed.empty:
            st.error("❌ No data after standardization")
            return pd.DataFrame()
        
        st.success(f"✅ Standardized {len(df_processed)} signals")
        
        # Step 2: Process outcomes from updates if available
        if df_updates is not None and not df_updates.empty:
            st.info(f"📝 Processing outcomes from {len(df_updates)} updates...")
            outcomes_df = process_signal_outcomes(df_updates)
            
            if not outcomes_df.empty:
                # Merge outcomes with signals
                df_processed = df_processed.merge(
                    outcomes_df[['signal_id', 'final_outcome', 'tp_level']], 
                    on='signal_id', 
                    how='left'
                )
                st.success(f"✅ Added outcomes for {outcomes_df['signal_id'].nunique()} signals")
            else:
                st.warning("⚠️ No outcomes could be processed from updates")
        else:
            st.info("ℹ️ No updates data available - using signals only")
        
        # Step 3: Add calculated fields
        df_processed = add_calculated_fields(df_processed)
        
        # Step 4: Final validation and cleanup
        df_final = final_data_cleanup(df_processed)
        
        st.success(f"🎉 Successfully processed {len(df_final)} signals with {df_final.columns.tolist()}")
        
        return df_final
        
    except Exception as e:
        st.error(f"❌ Signal processing failed: {e}")
        st.exception(e)
        return pd.DataFrame()

def standardize_signals_data(df):
    """Enhanced signal data standardization"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        # Step 1: Create working copy
        df_clean = df.copy()
        
        st.info("🔧 Standardizing column names...")
        
        # Step 2: Normalize column names
        column_mappings = {
            # Time columns (multiple variations)
            'timestamp': 'created_at',
            'time': 'created_at',
            'date': 'created_at',
            'create_time': 'created_at',
            'creation_date': 'created_at',
            
            # Pair columns
            'symbol': 'pair',
            'ticker': 'pair',
            'coin': 'pair',
            'trading_pair': 'pair',
            'currency_pair': 'pair',
            
            # Price columns
            'entry_price': 'entry',
            'buy_price': 'entry',
            
            # Target columns
            'tp1': 'target1',
            'tp2': 'target2', 
            'tp3': 'target3',
            'tp4': 'target4',
            'take_profit_1': 'target1',
            'take_profit_2': 'target2',
            'take_profit_3': 'target3',
            'take_profit_4': 'target4',
            
            # Stop loss columns
            'sl': 'stop1',
            'sl1': 'stop1',
            'sl2': 'stop2',
            'stop_loss': 'stop1',
            'stoploss': 'stop1'
        }
        
        # Apply column mappings
        df_clean = df_clean.rename(columns=column_mappings)
        
        st.info("📅 Standardizing datetime columns...")
        
        # Step 3: Handle datetime column with enhanced processing
        if 'created_at' in df_clean.columns:
            df_clean = standardize_datetime_column(df_clean, 'created_at')
        else:
            st.warning("⚠️ No datetime column found - using current time")
            df_clean['created_at'] = datetime.now()
        
        st.info("🏷️ Processing pair information...")
        
        # Step 4: Standardize pair column
        if 'pair' in df_clean.columns:
            df_clean['pair'] = df_clean['pair'].astype(str).str.upper().str.strip()
            df_clean['pair'] = df_clean['pair'].replace(['NAN', 'NONE', 'NULL'], 'UNKNOWN')
        else:
            df_clean['pair'] = 'UNKNOWN'
        
        st.info("🔢 Ensuring required columns...")
        
        # Step 5: Ensure all standard columns exist
        standard_columns = {
            'signal_id': 'string',
            'pair': 'string', 
            'created_at': 'datetime',
            'entry': 'float',
            'target1': 'float',
            'target2': 'float', 
            'target3': 'float',
            'target4': 'float',
            'stop1': 'float',
            'stop2': 'float',
            'final_outcome': 'string',
            'tp_level': 'int',
            'rr_planned': 'float',
            'is_open': 'boolean',
            'is_winner': 'boolean'
        }
        
        for col, dtype in standard_columns.items():
            if col not in df_clean.columns:
                if col == 'signal_id' and col not in df_clean.columns:
                    # Generate signal IDs if missing
                    df_clean['signal_id'] = [f"SIG_{i:06d}" for i in range(len(df_clean))]
                elif dtype == 'float':
                    df_clean[col] = np.nan
                elif dtype == 'int':
                    df_clean[col] = 0
                elif dtype == 'string':
                    df_clean[col] = None
                elif dtype == 'boolean':
                    df_clean[col] = False
        
        st.info("🧹 Cleaning and validating data...")
        
        # Step 6: Clean price data
        price_columns = ['entry', 'target1', 'target2', 'target3', 'target4', 'stop1', 'stop2']
        for col in price_columns:
            if col in df_clean.columns:
                # Convert to numeric
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                # Remove unrealistic values
                df_clean.loc[df_clean[col] <= 0, col] = np.nan
                df_clean.loc[df_clean[col] > 1000000, col] = np.nan
        
        # Step 7: Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Step 8: Remove duplicate signal IDs
        if 'signal_id' in df_clean.columns:
            initial_count = len(df_clean)
            df_clean = df_clean.drop_duplicates(subset=['signal_id'], keep='first')
            if len(df_clean) < initial_count:
                st.info(f"🔄 Removed {initial_count - len(df_clean)} duplicate signals")
        
        return df_clean
        
    except Exception as e:
        st.error(f"❌ Standardization failed: {e}")
        return pd.DataFrame()

def standardize_datetime_column(df, col):
    """
    Enhanced datetime standardization to prevent comparison errors
    """
    try:
        st.info(f"📅 Converting {col} to proper datetime format...")
        
        # Handle different datetime formats
        original_values = df[col].copy()
        
        # Method 1: Direct pandas conversion with UTC
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            success_count = df[col].notna().sum()
            st.info(f"✅ Converted {success_count}/{len(df)} datetime values")
        except Exception as e1:
            st.warning(f"Primary datetime conversion failed: {e1}")
            
            # Method 2: Try without UTC
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                success_count = df[col].notna().sum()
                st.info(f"✅ Fallback conversion successful: {success_count}/{len(df)}")
            except Exception as e2:
                st.error(f"Both datetime conversions failed: {e2}")
                # Fallback to current time
                df[col] = datetime.now()
        
        # Remove timezone info to prevent comparison issues
        if df[col].dtype.name.startswith('datetime') and hasattr(df[col].dtype, 'tz') and df[col].dtype.tz is not None:
            df[col] = df[col].dt.tz_localize(None)
            st.info("🌍 Removed timezone information to prevent comparison errors")
        
        # Fill any remaining NaT values
        nat_count = df[col].isna().sum()
        if nat_count > 0:
            st.warning(f"⚠️ Filling {nat_count} missing datetime values with current time")
            df[col] = df[col].fillna(datetime.now())
        
        return df
        
    except Exception as e:
        st.error(f"❌ Datetime standardization failed: {e}")
        # Ultimate fallback
        df[col] = datetime.now()
        return df

def process_signal_outcomes(df_updates):
    """Process outcomes from updates data"""
    if df_updates is None or df_updates.empty:
        return pd.DataFrame()
    
    try:
        st.info("🎯 Processing signal outcomes...")
        
        # Basic outcome inference
        outcome_data = []
        
        # Group by signal_id if available
        if 'signal_id' in df_updates.columns and 'update_type' in df_updates.columns:
            for signal_id in df_updates['signal_id'].unique():
                signal_updates = df_updates[df_updates['signal_id'] == signal_id]
                outcome = infer_outcome_from_updates(signal_updates)
                outcome_data.append({
                    'signal_id': signal_id,
                    'final_outcome': outcome['outcome'],
                    'tp_level': outcome['tp_level']
                })
        
        if outcome_data:
            outcomes_df = pd.DataFrame(outcome_data)
            st.success(f"✅ Processed outcomes for {len(outcomes_df)} signals")
            return outcomes_df
        else:
            st.warning("⚠️ No outcomes could be inferred from updates")
            return pd.DataFrame()
    
    except Exception as e:
        st.error(f"❌ Outcome processing failed: {e}")
        return pd.DataFrame()

def infer_outcome_from_updates(updates):
    """Infer outcome from signal updates"""
    try:
        if updates.empty:
            return {'outcome': None, 'tp_level': 0}
        
        # Look for TP and SL patterns
        update_types = updates['update_type'].str.lower().str.strip()
        
        # Check for TP hits (priority order)
        for tp_level in [4, 3, 2, 1]:
            tp_patterns = [f'tp{tp_level}', f'tp {tp_level}', f'target {tp_level}', f'target{tp_level}']
            if update_types.str.contains('|'.join(tp_patterns), na=False).any():
                return {'outcome': f'tp{tp_level}', 'tp_level': tp_level}
        
        # Check for SL hit
        sl_patterns = ['sl', 'stop', 'stop loss', 'stoploss']
        if update_types.str.contains('|'.join(sl_patterns), na=False).any():
            return {'outcome': 'sl', 'tp_level': 0}
        
        # Default to open
        return {'outcome': None, 'tp_level': 0}
        
    except Exception as e:
        return {'outcome': None, 'tp_level': 0}

def add_calculated_fields(df):
    """Add calculated fields with error handling"""
    try:
        st.info("🔢 Adding calculated fields...")
        
        # Add is_open flag
        if 'final_outcome' in df.columns:
            df['is_open'] = df['final_outcome'].isna() | (df['final_outcome'] == 'open') | (df['final_outcome'] == '')
        else:
            df['is_open'] = True
        
        # Add is_winner flag  
        if 'final_outcome' in df.columns:
            df['is_winner'] = df['final_outcome'].str.startswith('tp', na=False)
        else:
            df['is_winner'] = False
        
        # Calculate TP level if not already present
        if 'tp_level' not in df.columns or df['tp_level'].isna().all():
            df['tp_level'] = 0
            if 'final_outcome' in df.columns:
                for i in range(1, 5):
                    mask = df['final_outcome'] == f'tp{i}'
                    df.loc[mask, 'tp_level'] = i
        
        # Calculate RR ratios
        df = calculate_rr_ratios(df)
        
        st.success("✅ Added calculated fields successfully")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Failed to add calculated fields: {e}")
        return df

def calculate_rr_ratios(df):
    """Calculate risk-reward ratios"""
    try:
        if not all(col in df.columns for col in ['entry', 'stop1']):
            st.warning("⚠️ Missing required columns for RR calculation")
            df['rr_planned'] = np.nan
            return df
        
        # Use stop1 as primary, fallback to stop2
        df['stop_used'] = df['stop1'].fillna(df['stop2'])
        
        # Calculate risk distance (entry to stop)
        df['risk_distance'] = abs(df['entry'] - df['stop_used'])
        
        # Find highest target
        target_cols = ['target4', 'target3', 'target2', 'target1']
        df['highest_target'] = np.nan
        
        for target_col in target_cols:
            if target_col in df.columns:
                mask = df[target_col].notna() & df['highest_target'].isna()
                df.loc[mask, 'highest_target'] = df.loc[mask, target_col]
        
        # Calculate planned RR
        reward_distance = abs(df['highest_target'] - df['entry'])
        df['rr_planned'] = np.where(
            (df['risk_distance'] > 0) & df['risk_distance'].notna() & reward_distance.notna(),
            reward_distance / df['risk_distance'],
            np.nan
        )
        
        # Clean up temporary columns
        df = df.drop(columns=['stop_used', 'risk_distance', 'highest_target'], errors='ignore')
        
        rr_count = df['rr_planned'].notna().sum()
        st.info(f"📊 Calculated RR for {rr_count} signals")
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ RR calculation failed: {e}")
        if 'rr_planned' not in df.columns:
            df['rr_planned'] = np.nan
        return df

def final_data_cleanup(df):
    """Final data cleanup and validation"""
    try:
        st.info("🧹 Final data cleanup...")
        
        # Remove rows with no essential data
        essential_cols = ['signal_id', 'pair']
        for col in essential_cols:
            if col in df.columns:
                initial_len = len(df)
                df = df[df[col].notna()]
                if len(df) < initial_len:
                    st.info(f"🗑️ Removed {initial_len - len(df)} rows with missing {col}")
        
        # Sort by created_at if available
        if 'created_at' in df.columns:
            df = df.sort_values('created_at', ascending=False)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        st.success(f"🎉 Final cleanup complete: {len(df)} clean signals ready")
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ Final cleanup had issues: {e}")
        return df
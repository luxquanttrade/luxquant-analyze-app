"""
Data Standardization Module
Standardizes all data before processing to prevent errors and ensure consistency
"""
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataStandardizer:
    """Comprehensive data standardization for trading signals"""
    
    def __init__(self):
        self.standard_columns = {
            # Core signal data
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
            
            # Outcome data
            'final_outcome': 'string',
            'tp_level': 'int',
            
            # Calculated fields
            'rr_planned': 'float',
            'rr_realized': 'float',
            'is_open': 'boolean',
            'is_winner': 'boolean'
        }
        
        self.required_columns = ['signal_id', 'pair', 'created_at']
    
    def standardize_signals_data(self, df):
        """Standardize signals data with comprehensive error handling"""
        if df is None or df.empty:
            logger.warning("Empty signals data provided")
            return self._create_empty_signals_df()
        
        logger.info(f"Standardizing signals data: {len(df)} rows, {len(df.columns)} columns")
        
        try:
            # Create working copy
            standardized_df = df.copy()
            
            # 1. Standardize column names
            standardized_df = self._standardize_column_names(standardized_df)
            
            # 2. Ensure required columns exist
            standardized_df = self._ensure_required_columns(standardized_df)
            
            # 3. Standardize data types
            standardized_df = self._standardize_data_types(standardized_df)
            
            # 4. Clean and validate data
            standardized_df = self._clean_data(standardized_df)
            
            # 5. Add calculated fields
            standardized_df = self._add_calculated_fields(standardized_df)
            
            logger.info(f"Standardization complete: {len(standardized_df)} rows retained")
            return standardized_df
            
        except Exception as e:
            logger.error(f"Standardization failed: {e}")
            return self._create_empty_signals_df()
    
    def _standardize_column_names(self, df):
        """Standardize column names to consistent format"""
        # Common column mappings
        column_mappings = {
            # Time columns
            'timestamp': 'created_at',
            'time': 'created_at',
            'date': 'created_at',
            'create_time': 'created_at',
            
            # Pair columns
            'symbol': 'pair',
            'ticker': 'pair',
            'coin': 'pair',
            'trading_pair': 'pair',
            
            # Price columns
            'entry_price': 'entry',
            'buy_price': 'entry',
            'sell_price': 'entry',
            
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
            'stoploss': 'stop1',
            
            # Outcome columns
            'outcome': 'final_outcome',
            'result': 'final_outcome',
            'status': 'final_outcome'
        }
        
        # Apply mappings
        df_renamed = df.rename(columns=column_mappings)
        
        # Normalize column names (lowercase, remove spaces/special chars)
        normalized_columns = {}
        for col in df_renamed.columns:
            normalized = col.lower().strip().replace(' ', '_').replace('-', '_')
            if normalized != col:
                normalized_columns[col] = normalized
        
        if normalized_columns:
            df_renamed = df_renamed.rename(columns=normalized_columns)
        
        return df_renamed
    
    def _ensure_required_columns(self, df):
        """Ensure all required columns exist"""
        for col in self.required_columns:
            if col not in df.columns:
                if col == 'signal_id':
                    # Generate signal IDs if missing
                    df['signal_id'] = [f"SIG_{i:06d}" for i in range(len(df))]
                elif col == 'pair':
                    df['pair'] = 'UNKNOWN'
                elif col == 'created_at':
                    df['created_at'] = datetime.now()
        
        # Ensure all standard columns exist
        for col, dtype in self.standard_columns.items():
            if col not in df.columns:
                if dtype == 'float':
                    df[col] = np.nan
                elif dtype == 'int':
                    df[col] = 0
                elif dtype == 'string':
                    df[col] = None
                elif dtype == 'boolean':
                    df[col] = False
                elif dtype == 'datetime':
                    df[col] = pd.NaT
        
        return df
    
    def _standardize_data_types(self, df):
        """Standardize data types for all columns"""
        df_typed = df.copy()
        
        for col, target_type in self.standard_columns.items():
            if col not in df_typed.columns:
                continue
                
            try:
                if target_type == 'datetime':
                    # Comprehensive datetime standardization
                    df_typed[col] = self._standardize_datetime(df_typed[col])
                    
                elif target_type == 'float':
                    # Convert to numeric, coerce errors to NaN
                    df_typed[col] = pd.to_numeric(df_typed[col], errors='coerce')
                    
                elif target_type == 'int':
                    # Convert to int, handle NaN
                    numeric_col = pd.to_numeric(df_typed[col], errors='coerce')
                    df_typed[col] = numeric_col.fillna(0).astype(int)
                    
                elif target_type == 'string':
                    # Convert to string, handle nulls
                    df_typed[col] = df_typed[col].astype(str)
                    df_typed[col] = df_typed[col].replace('nan', None)
                    df_typed[col] = df_typed[col].replace('None', None)
                    
                elif target_type == 'boolean':
                    # Convert to boolean
                    df_typed[col] = df_typed[col].astype(bool)
                    
            except Exception as e:
                logger.warning(f"Failed to convert {col} to {target_type}: {e}")
                continue
        
        return df_typed
    
    def _standardize_datetime(self, series):
        """Comprehensive datetime standardization"""
        try:
            # First attempt: direct conversion
            dt_series = pd.to_datetime(series, errors='coerce')
            
            # Remove timezone information to prevent comparison issues
            if dt_series.dt.tz is not None:
                dt_series = dt_series.dt.tz_localize(None)
            
            # Fill missing values with current time
            dt_series = dt_series.fillna(datetime.now())
            
            return dt_series
            
        except Exception as e:
            logger.warning(f"DateTime standardization failed: {e}")
            # Fallback: return current time for all values
            return pd.Series([datetime.now()] * len(series), index=series.index)
    
    def _clean_data(self, df):
        """Clean and validate data"""
        df_clean = df.copy()
        
        # 1. Clean pair names
        if 'pair' in df_clean.columns:
            df_clean['pair'] = df_clean['pair'].str.upper()
            df_clean['pair'] = df_clean['pair'].str.replace(' ', '')
            df_clean['pair'] = df_clean['pair'].fillna('UNKNOWN')
        
        # 2. Validate price fields
        price_columns = ['entry', 'target1', 'target2', 'target3', 'target4', 'stop1', 'stop2']
        for col in price_columns:
            if col in df_clean.columns:
                # Remove negative prices
                df_clean.loc[df_clean[col] < 0, col] = np.nan
                # Remove unreasonably high prices (> 1 million)
                df_clean.loc[df_clean[col] > 1000000, col] = np.nan
        
        # 3. Clean outcome field
        if 'final_outcome' in df_clean.columns:
            df_clean['final_outcome'] = df_clean['final_outcome'].str.lower()
            df_clean['final_outcome'] = df_clean['final_outcome'].str.strip()
            
            # Standardize outcome values
            outcome_mappings = {
                'tp_1': 'tp1',
                'tp_2': 'tp2', 
                'tp_3': 'tp3',
                'tp_4': 'tp4',
                'target_1': 'tp1',
                'target_2': 'tp2',
                'target_3': 'tp3', 
                'target_4': 'tp4',
                'stop_loss': 'sl',
                'stoploss': 'sl'
            }
            df_clean['final_outcome'] = df_clean['final_outcome'].replace(outcome_mappings)
        
        # 4. Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # 5. Remove duplicate signal IDs
        if 'signal_id' in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=['signal_id'], keep='first')
        
        return df_clean
    
    def _add_calculated_fields(self, df):
        """Add calculated fields based on existing data"""
        df_calc = df.copy()
        
        try:
            # 1. Calculate is_open flag
            if 'final_outcome' in df_calc.columns:
                df_calc['is_open'] = df_calc['final_outcome'].isna() | (df_calc['final_outcome'] == 'open')
            
            # 2. Calculate is_winner flag  
            if 'final_outcome' in df_calc.columns:
                df_calc['is_winner'] = df_calc['final_outcome'].str.startswith('tp', na=False)
            
            # 3. Calculate TP level
            if 'final_outcome' in df_calc.columns:
                df_calc['tp_level'] = 0
                for i in range(1, 5):
                    mask = df_calc['final_outcome'] == f'tp{i}'
                    df_calc.loc[mask, 'tp_level'] = i
            
            # 4. Calculate basic RR ratios
            if all(col in df_calc.columns for col in ['entry', 'target1', 'stop1']):
                df_calc = self._calculate_rr_ratios(df_calc)
            
        except Exception as e:
            logger.warning(f"Failed to add calculated fields: {e}")
        
        return df_calc
    
    def _calculate_rr_ratios(self, df):
        """Calculate risk-reward ratios"""
        try:
            # Use stop1 as primary stop, fallback to stop2
            df['stop_used'] = df['stop1'].fillna(df['stop2'])
            
            # Calculate risk distance
            df['risk_distance'] = abs(df['entry'] - df['stop_used'])
            
            # Calculate RR for each target
            for i in range(1, 5):
                target_col = f'target{i}'
                rr_col = f'rr_target{i}'
                
                if target_col in df.columns:
                    reward_distance = abs(df[target_col] - df['entry'])
                    df[rr_col] = np.where(
                        (df['risk_distance'] > 0) & df['risk_distance'].notna() & reward_distance.notna(),
                        reward_distance / df['risk_distance'],
                        np.nan
                    )
            
            # Overall planned RR (using highest available target)
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
            
        except Exception as e:
            logger.warning(f"RR calculation failed: {e}")
        
        return df
    
    def _create_empty_signals_df(self):
        """Create empty standardized DataFrame"""
        empty_data = {}
        
        for col, dtype in self.standard_columns.items():
            if dtype == 'float':
                empty_data[col] = pd.Series([], dtype='float64')
            elif dtype == 'int':
                empty_data[col] = pd.Series([], dtype='int64')
            elif dtype == 'string':
                empty_data[col] = pd.Series([], dtype='object')
            elif dtype == 'boolean':
                empty_data[col] = pd.Series([], dtype='bool')
            elif dtype == 'datetime':
                empty_data[col] = pd.Series([], dtype='datetime64[ns]')
        
        return pd.DataFrame(empty_data)
    
    def get_data_quality_report(self, df):
        """Generate data quality report"""
        if df is None or df.empty:
            return {"status": "empty", "issues": ["No data available"]}
        
        report = {
            "status": "good",
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "issues": [],
            "warnings": [],
            "column_info": {}
        }
        
        # Check data completeness
        for col in self.required_columns:
            if col not in df.columns:
                report["issues"].append(f"Missing required column: {col}")
                report["status"] = "issues"
            else:
                null_pct = (df[col].isna().sum() / len(df) * 100)
                if null_pct > 50:
                    report["warnings"].append(f"High null percentage in {col}: {null_pct:.1f}%")
                    report["status"] = "warnings" if report["status"] == "good" else report["status"]
        
        # Column completeness
        for col in df.columns:
            if col in self.standard_columns:
                null_count = df[col].isna().sum()
                null_pct = (null_count / len(df) * 100)
                report["column_info"][col] = {
                    "type": str(df[col].dtype),
                    "null_count": null_count,
                    "null_percentage": round(null_pct, 2),
                    "unique_values": df[col].nunique()
                }
        
        return report

# Factory function
def create_standardizer():
    """Create and return a DataStandardizer instance"""
    return DataStandardizer()
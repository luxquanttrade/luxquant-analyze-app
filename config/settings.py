"""
Configuration settings for LuxQuant Analyzer
"""

# Page configuration
PAGE_CONFIG = {
    "page_title": "LuxQuant Signals Analyzer",
    "layout": "wide"
}

# Database table name mappings
TABLE_MAPPINGS = {
    "signals": ["signals", "signal", "trading_signals"],
    "updates": ["signal_updates", "updates", "signal_update_log"],
    "fills": ["executions", "fills", "signal_fills"]
}

# Column name mappings for flexible data handling
COLUMN_MAPPINGS = {
    "created_at": ["created_at", "timestamp", "time", "date"],
    "pair": ["pair", "symbol", "ticker", "coin"],
    "update_type": ["update_type", "status", "type", "event", "outcome"],
    "time": ["update_at", "created_at", "timestamp", "time"]
}

# Required columns for signals table
REQUIRED_SIGNAL_COLUMNS = [
    "signal_id", "pair", "entry", "target1", "target2", 
    "target3", "target4", "stop1", "stop2"
]

# Outcome ranking for TP levels
OUTCOME_RANKING = {
    "sl": 0,
    "tp1": 1, 
    "tp2": 2,
    "tp3": 3,
    "tp4": 4
}

# Chart colors
CHART_COLORS = {
    "primary": "#1f77b4",
    "success": "#2ca02c", 
    "danger": "#d62728",
    "warning": "#ff7f0e",
    "info": "#17becf"
}

# Display settings
DISPLAY_SETTINGS = {
    "decimal_places": 4,
    "min_pair_signals": 3,  # Minimum signals required to show pair stats
    "top_pairs_limit": 15   # Max pairs to show in charts
}
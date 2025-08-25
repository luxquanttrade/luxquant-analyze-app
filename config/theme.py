"""
Dark theme configuration for LuxQuant Analyzer
"""

# Color Palette
COLORS = {
    # Primary colors
    "background": "#0E1117",
    "card_bg": "#1A1D24",
    "card_border": "#2D3139",
    
    # Text colors
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A0A0",
    "text_muted": "#6B6B6B",
    
    # Accent colors
    "green": "#00D46A",
    "red": "#FF4747", 
    "yellow": "#FDB32B",
    "blue": "#4B9BFF",
    "purple": "#9D5CFF",
    
    # Chart colors
    "chart_green": "#00D46A",
    "chart_red": "#FF4747",
    "chart_yellow": "#FDB32B",
    "chart_blue": "#4B9BFF",
    "chart_purple": "#9D5CFF",
    "chart_grid": "#2D3139",
    
    # Status colors
    "success": "#00D46A",
    "danger": "#FF4747",
    "warning": "#FDB32B",
    "info": "#4B9BFF",
}

# Custom CSS for dark theme
CUSTOM_CSS = """
<style>
/* Main app background */
.stApp {
    background-color: #0E1117;
}

/* Metrics styling */
[data-testid="metric-container"] {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

[data-testid="metric-container"] [data-testid="metric-label"] {
    color: #A0A0A0;
    font-size: 14px;
    font-weight: 500;
}

[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: 700;
}

[data-testid="metric-container"] [data-testid="metric-delta"] {
    font-size: 14px;
}

/* Card styling */
.custom-card {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

/* Success/Error messages */
.stSuccess {
    background-color: rgba(0, 212, 106, 0.1);
    border: 1px solid #00D46A;
    color: #00D46A;
}

.stError {
    background-color: rgba(255, 71, 71, 0.1);
    border: 1px solid #FF4747;
    color: #FF4747;
}

.stWarning {
    background-color: rgba(253, 178, 43, 0.1);
    border: 1px solid #FDB32B;
    color: #FDB32B;
}

/* Dataframe styling */
[data-testid="stDataFrameResizable"] {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    border-radius: 8px;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #1A1D24;
    border-right: 1px solid #2D3139;
}

/* Headers */
h1, h2, h3 {
    color: #FFFFFF !important;
}

/* Expander */
.streamlit-expanderHeader {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    border-radius: 8px;
}

/* Buttons */
.stButton > button {
    background-color: #2D3139;
    color: #FFFFFF;
    border: 1px solid #3D4149;
    border-radius: 8px;
    transition: all 0.3s;
}

.stButton > button:hover {
    background-color: #3D4149;
    border-color: #4D5159;
}

/* Select boxes */
.stSelectbox > div > div {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
}

/* Progress bar */
.stProgress > div > div > div {
    background-color: #00D46A;
}

/* Custom classes */
.metric-card {
    background: linear-gradient(135deg, #1A1D24 0%, #252831 100%);
    border: 1px solid #2D3139;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.4);
}

.green-text { color: #00D46A !important; }
.red-text { color: #FF4747 !important; }
.yellow-text { color: #FDB32B !important; }

/* Charts background */
.js-plotly-plot {
    background-color: #1A1D24 !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1A1D24;
}

::-webkit-scrollbar-thumb {
    background: #2D3139;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #3D4149;
}
</style>
"""

# Plotly dark theme configuration
PLOTLY_CONFIG = {
    "template": "plotly_dark",
    "paper_bgcolor": "#1A1D24",
    "plot_bgcolor": "#1A1D24",
    "font": {
        "color": "#FFFFFF",
        "family": "Inter, sans-serif"
    },
    "xaxis": {
        "gridcolor": "#2D3139",
        "linecolor": "#2D3139",
        "tickfont": {"color": "#A0A0A0"}
    },
    "yaxis": {
        "gridcolor": "#2D3139", 
        "linecolor": "#2D3139",
        "tickfont": {"color": "#A0A0A0"}
    },
    "colorway": ["#00D46A", "#FF4747", "#FDB32B", "#4B9BFF", "#9D5CFF"]
}

# Chart specific configs
CHART_CONFIGS = {
    "winrate_trend": {
        "line_color": "#00D46A",
        "fill_color": "rgba(0, 212, 106, 0.1)",
        "grid_color": "#2D3139"
    },
    "bar_chart": {
        "positive_color": "#00D46A",
        "negative_color": "#FF4747",
        "neutral_color": "#FDB32B"
    },
    "gauge": {
        "steps": [
            {"range": [0, 20], "color": "#FF4747"},
            {"range": [20, 40], "color": "#FF8C42"},
            {"range": [40, 60], "color": "#FDB32B"},
            {"range": [60, 80], "color": "#7FD46A"},
            {"range": [80, 100], "color": "#00D46A"}
        ],
        "threshold": {
            "line": {"color": "white", "width": 2},
            "thickness": 0.75,
            "value": 50
        }
    }
}

# Metric card templates
METRIC_CARD_TEMPLATE = """
<div class="metric-card" style="text-align: center;">
    <p style="color: #A0A0A0; font-size: 14px; margin: 0;">{label}</p>
    <h2 style="color: {color}; margin: 10px 0; font-size: 32px; font-weight: 700;">{value}</h2>
    <p style="color: {delta_color}; font-size: 12px; margin: 0;">{delta}</p>
</div>
"""

# Performance card template
PERFORMANCE_CARD_TEMPLATE = """
<div class="custom-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="color: #FFFFFF; margin: 0;">{title}</h3>
        <span style="color: {value_color}; font-size: 24px; font-weight: 700;">{value}</span>
    </div>
    <div style="margin-top: 10px;">
        {content}
    </div>
</div>
"""
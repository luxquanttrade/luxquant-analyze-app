"""
🔮 Call Prediction - LuxQuant Pro v2
AI-powered analysis and recommendations for trading calls
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from datetime import datetime
import sys
import os

# Page config
st.set_page_config(
    page_title="🔮 Call Prediction - LuxQuant Pro",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Model Loading
try:
    from joblib import load
    
    @st.cache_resource
    def load_tp_bundle():
        """Load the ML model bundle"""
        possible_paths = [
            "luxquant_tp_twostagенew_bundle.joblib",
            "luxquant_tp_twostage_bundle.joblib",
        ]
        
        for path in possible_paths:
            try:
                bundle = load(path)
                st.success(f"✅ ML Model loaded: {path}")
                return bundle
            except FileNotFoundError:
                continue
            except Exception as e:
                st.warning(f"⚠️ Error loading {path}: {str(e)}")
                continue
        
        st.error("❌ Could not load ML model file")
        return None
    
    ML_BUNDLE = load_tp_bundle()
except ImportError:
    st.error("❌ joblib not available")
    ML_BUNDLE = None

# Import modules with error handling
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.connection import get_connection_status, load_data
    from data_processing.signal_processor import process_signals
    from config.theme import COLORS, CUSTOM_CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
except ImportError:
    # Fallback colors
    COLORS = {
        "green": "#00D46A",
        "red": "#FF4747", 
        "blue": "#4B9BFF",
        "yellow": "#FDB32B",
        "purple": "#9D5CFF",
        "background": "#0E1117"
    }

# Text parsing patterns
PAIR_PAT = re.compile(r"NEW\s*CALL:\s*([A-Z0-9_]+USDT)", re.IGNORECASE)
VOL_PAT = re.compile(r"Volume\(24H\)\s*Ranked:\s*(?:🏅\s*)?(\d+)(?:st|nd|rd|th)?/(\d+)", re.IGNORECASE)
RISK_PAT = re.compile(r"Risk\s*Level\s*[:\-]?\s*(?:⚠️\s*)?([A-Za-z]+)", re.IGNORECASE)
ENTRY_PAT = re.compile(r"Entry\s*:\s*([0-9]+(?:[\.,][0-9]+)?)", re.IGNORECASE)

def parse_call_text(call_text: str):
    """Parse trading call text and extract data"""
    text = call_text.replace("**", " ").replace("__", " ").strip()
    
    # Extract pair
    m = PAIR_PAT.search(text)
    if not m:
        m = re.search(r"\b([A-Z0-9]{2,}USDT)\b", text)
    pair = m.group(1).upper() if m else None

    # Extract entry price
    m = ENTRY_PAT.search(text)
    entry = float(m.group(1).replace(",", ".")) if m else None

    # Extract volume ranking
    m = VOL_PAT.search(text)
    vol_num = int(m.group(1)) if m else None
    vol_den = int(m.group(2)) if m else None

    # Extract risk level
    risk = None
    m = RISK_PAT.search(text)
    if m:
        raw = m.group(1).strip().lower()
        if "high" in raw or "tinggi" in raw or "red" in raw:
            risk = "High"
        elif "medium" in raw or "mid" in raw or "yellow" in raw:
            risk = "Medium"
        elif "low" in raw or "rendah" in raw or "green" in raw or "normal" in raw:
            risk = "Low"

    # Extract targets
    target_patterns = [
        r'Target\s*1\s*[\s]*([0-9]+(?:[\.,][0-9]+)?)',
        r'Target\s*2\s*[\s]*([0-9]+(?:[\.,][0-9]+)?)',
        r'Target\s*3\s*[\s]*([0-9]+(?:[\.,][0-9]+)?)',
        r'Target\s*4\s*[\s]*([0-9]+(?:[\.,][0-9]+)?)'
    ]
    
    targets = {}
    for i, pattern in enumerate(target_patterns, 1):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            targets[i] = float(match.group(1).replace(',', '.'))

    # Extract stops
    stop_patterns = [
        r'Stop\s*Loss\s*1\s*[\s]*([0-9]+(?:[\.,][0-9]+)?)',
        r'Stop\s*Loss\s*2\s*[\s]*([0-9]+(?:[\.,][0-9]+)?)'
    ]
    
    stops = {}
    for i, pattern in enumerate(stop_patterns, 1):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stops[i] = float(match.group(1).replace(',', '.'))

    return {
        "pair": pair,
        "entry": entry,
        "volume_rank_num": vol_num,
        "volume_rank_den": vol_den,
        "risk_level": risk,
        "targets": targets,
        "stops": stops
    }

def build_feature_row_from_text(parsed: dict, num_cols, cat_cols):
    """Build feature row for ML model"""
    if not ML_BUNDLE:
        return pd.DataFrame(), {}
    
    # Basic features
    volume_rank_score = np.nan
    if parsed.get("volume_rank_num") and parsed.get("volume_rank_den"):
        if parsed["volume_rank_den"] > 0:
            volume_rank_score = 1 - (parsed["volume_rank_num"] / parsed["volume_rank_den"])
    
    risk_map = {"Low": 0, "Medium": 1, "High": 2}
    risk_num = risk_map.get(parsed.get("risk_level"), np.nan)

    entry = parsed.get("entry", np.nan)
    targets = parsed.get("targets", {})
    stops = parsed.get("stops", {})

    # Initialize feature row
    row = {
        "entry": entry,
        "volume_rank_score": volume_rank_score,
        "risk_num": risk_num,
        "hour": np.nan,
        "dow": np.nan,
        "pair": parsed.get("pair"),
    }

    # Target percentage features
    for i in range(1, 5):
        if i in targets and entry and not np.isnan(entry):
            row[f"tp{i}_pct"] = ((targets[i] - entry) / entry) * 100
        else:
            row[f"tp{i}_pct"] = np.nan

    # Stop loss percentage features
    for i in range(1, 3):
        if i in stops and entry and not np.isnan(entry):
            row[f"sl{i}_pct"] = ((stops[i] - entry) / entry) * 100
        else:
            row[f"sl{i}_pct"] = np.nan

    # Risk-Reward ratios
    sl1 = stops.get(1)
    if sl1 and entry and not np.isnan(entry):
        risk_amount = abs(entry - sl1)
        for i in range(1, 5):
            if i in targets:
                reward_amount = abs(targets[i] - entry)
                row[f"RR{i}"] = reward_amount / risk_amount if risk_amount > 0 else np.nan
            else:
                row[f"RR{i}"] = np.nan
    else:
        for i in range(1, 5):
            row[f"RR{i}"] = np.nan

    # Target spacing features
    valid_targets = [targets[i] for i in sorted(targets.keys()) if i in targets]
    if len(valid_targets) >= 2:
        spacings = [valid_targets[i] - valid_targets[i-1] for i in range(1, len(valid_targets))]
        row["spacing"] = np.mean(spacings) / entry if entry and not np.isnan(entry) else np.nan
        row["tightness"] = np.std(spacings) / entry if entry and not np.isnan(entry) and len(spacings) > 1 else np.nan
    else:
        row["spacing"] = np.nan
        row["tightness"] = np.nan

    # Summary statistics
    tp_values = [row[f"tp{i}_pct"] for i in range(1, 5) if not np.isnan(row[f"tp{i}_pct"])]
    if tp_values:
        row["tp_mean"] = np.mean(tp_values)
        row["tp_max"] = np.max(tp_values)
        row["tp_std"] = np.std(tp_values) if len(tp_values) > 1 else 0
    else:
        row["tp_mean"] = np.nan
        row["tp_max"] = np.nan
        row["tp_std"] = np.nan

    X = pd.DataFrame([row])
    
    # Ensure columns match training data
    for c in num_cols + cat_cols:
        if c not in X.columns:
            X[c] = np.nan
    
    return X[num_cols + cat_cols], targets

def eff_threshold(X_row, base=0.32):
    """Calculate effective threshold"""
    try:
        volume_rank_score = X_row.iloc[0].get('volume_rank_score', 0.5) if not X_row.empty else 0.5
        risk_num = X_row.iloc[0].get('risk_num', 1) if not X_row.empty else 1
        tp1_pct = X_row.iloc[0].get('tp1_pct', 5) if not X_row.empty else 5
        
        threshold_adj = 0
        
        # Volume adjustment
        if volume_rank_score < 0.3:
            threshold_adj += 0.05
        
        # Risk adjustment
        if risk_num >= 2:
            threshold_adj += 0.03
        
        # TP1 adjustment
        if not np.isnan(tp1_pct) and tp1_pct < 2:
            threshold_adj += 0.04
        
        return base + threshold_adj
    except:
        return base

def predict_min_tp_from_text(call_text: str, bundle: dict):
    """Predict using ML model"""
    if bundle is None:
        return {
            "error": "ML model not loaded",
            "predicted_min_tp": None,
            "confidence": 0
        }
    
    try:
        parsed = parse_call_text(call_text)
        X_row, targets = build_feature_row_from_text(parsed, bundle["num_cols"], bundle["cat_cols"])
        X_row = X_row.fillna(0)

        # Get thresholds
        base = bundle.get("stageA_threshold", 0.32)
        band = bundle.get("policy_band", 0.08)
        th_eff = eff_threshold(X_row, base=base)

        # Stage A prediction
        p_hit = float(bundle["pipe_A"].predict_proba(X_row)[0, 1])
        th_lo, th_hi = base, base + band
        go_hit = p_hit >= max(th_hi, th_eff)

        if go_hit:
            # Stage B
            pred_m = int(bundle["pipe_B"].predict(X_row)[0])
            pred = int(bundle["inv_map_B"][pred_m])
        else:
            # Stage C
            sl_bin = int(bundle["pipe_C"].predict(X_row)[0])
            pred = -1 if sl_bin == 1 else 0

        # Get recommended price
        entry = parsed.get("entry")
        price_reco = targets.get(pred) if (pred > 0 and isinstance(targets, dict)) else None
        change_reco = ((price_reco - entry) / entry * 100) if (entry and price_reco) else None

        return {
            "pair": parsed.get("pair"),
            "entry": entry,
            "volume_rank": (parsed.get("volume_rank_num"), parsed.get("volume_rank_den")),
            "risk_level": parsed.get("risk_level"),
            "predicted_min_tp": pred,
            "recommended_price": price_reco,
            "recommended_change_pct": change_reco,
            "p_hit_stageA": p_hit,
            "threshold_used_base": base,
            "threshold_used_band": band,
            "threshold_used_effective": th_eff,
            "confidence": p_hit,
            "targets_parsed": targets,
            "go_hit_decision": go_hit
        }
    
    except Exception as e:
        return {
            "error": f"Prediction failed: {str(e)}",
            "predicted_min_tp": None,
            "confidence": 0
        }

def get_historical_performance(pair, data):
    """Get historical performance data"""
    try:
        if data is None or data.empty or 'pair' not in data.columns:
            return None
        
        pair_data = data[data['pair'] == pair]
        if pair_data.empty:
            return None
        
        closed_trades = pair_data[pair_data['final_outcome'].notna()]
        if closed_trades.empty:
            return None
        
        metrics = {
            'total_signals': len(pair_data),
            'closed_trades': len(closed_trades),
            'tp1_hits': (closed_trades['final_outcome'] == 'tp1').sum(),
            'tp2_hits': (closed_trades['final_outcome'] == 'tp2').sum(),
            'tp3_hits': (closed_trades['final_outcome'] == 'tp3').sum(),
            'tp4_hits': (closed_trades['final_outcome'] == 'tp4').sum(),
            'sl_hits': (closed_trades['final_outcome'] == 'sl').sum(),
        }
        
        total_closed = metrics['closed_trades']
        if total_closed > 0:
            metrics['tp1_prob'] = metrics['tp1_hits'] / total_closed
            metrics['tp2_prob'] = metrics['tp2_hits'] / total_closed
            metrics['tp3_prob'] = metrics['tp3_hits'] / total_closed
            metrics['tp4_prob'] = metrics['tp4_hits'] / total_closed
            metrics['sl_prob'] = metrics['sl_hits'] / total_closed
            metrics['overall_wr'] = (metrics['tp1_hits'] + metrics['tp2_hits'] + 
                                   metrics['tp3_hits'] + metrics['tp4_hits']) / total_closed
        
        return metrics
    except Exception:
        return None

def tp_label(tp_int: int):
    """Map TP integer to label"""
    return {
        -1: "SL (Stop Loss)",
        0: "No Clear Outcome", 
        1: "TP1",
        2: "TP2",
        3: "TP3",
        4: "TP4"
    }.get(tp_int, "Unknown")

def tp_emoji(tp_int: int):
    """Get emoji for TP level"""
    return {
        -1: "🔻",
        0: "❓",
        1: "🎯",
        2: "🎯🎯", 
        3: "🎯🎯🎯",
        4: "🎯🎯🎯🎯"
    }.get(tp_int, "❓")

def render_page_header():
    """Render page header"""
    st.markdown("""
    <div style="margin-bottom: 30px;">
        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">
            🔮 Call Prediction v2
        </h1>
        <p style="color: #A0A0A0; font-size: 16px; margin-top: 10px;">
            Enhanced ML model with target structure analysis & dynamic thresholding
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_prediction_sidebar():
    """Render sidebar controls"""
    st.sidebar.title("🔮 AI Prediction v2")
    
    st.sidebar.markdown("""
    **Model v2 Features:**
    - Two-stage calibrated pipeline
    - Target structure analysis
    - Dynamic threshold adjustment
    - Price recommendation output
    """)
    
    # Model status
    if ML_BUNDLE:
        st.sidebar.success("🤖 ML Model v2: LOADED")
        try:
            num_features = len(ML_BUNDLE.get('num_cols', []) + ML_BUNDLE.get('cat_cols', []))
            st.sidebar.caption(f"Features: {num_features}")
            
            base_threshold = ML_BUNDLE.get('stageA_threshold', 0.32)
            policy_band = ML_BUNDLE.get('policy_band', 0.08)
            
            st.sidebar.caption(f"Base threshold: {base_threshold:.3f}")
            st.sidebar.caption(f"Policy band: {policy_band:.3f}")
        except:
            st.sidebar.caption("Model details unavailable")
    else:
        st.sidebar.error("❌ ML Model v2: NOT LOADED")
    
    # Settings
    st.sidebar.subheader("⚙️ Settings")
    
    show_technical_details = st.sidebar.checkbox(
        "Show Technical Details",
        value=False,
        help="Display threshold calculations and feature breakdown"
    )
    
    risk_adjustment = st.sidebar.selectbox(
        "Risk Profile",
        ["Conservative", "Balanced", "Aggressive"],
        index=1,
        help="Adjust interpretation based on risk appetite"
    )
    
    return {
        'show_technical_details': show_technical_details,
        'risk_adjustment': risk_adjustment
    }

def render_call_input():
    """Render call input section"""
    st.subheader("📝 Trading Call Input")
    
    sample_call = """🆕 NEW CALL: BERAUSDT 🆕

📊 Risk Analysis 📊
Volume(24H) Ranked: 81th/517
Risk Level: 🟢 Normal

**Entry: 2.453**

📝 Targets & Stop Loss
---------------------------------------
Level         Price       % Change from Entry
---------------------------------------
Target 1         2.503      +2.04%
Target 2         2.553      +4.08%
Target 3         2.703      +10.19%
Target 4         2.952      +20.34%
Stop Loss 1    2.332      -4.93%
Stop Loss 2    2.053      -16.31%
---------------------------------------

🔍Sentimen $BERA
📊 Data Coinglass $BERA"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        call_text = st.text_area(
            "Paste your trading call here:",
            value=sample_call,
            height=400,
            help="Paste the complete trading call text for analysis"
        )
        
        analyze_button = st.button("🔮 Analyze Call", type="primary", use_container_width=True)
        
        return call_text, analyze_button
    
    with col2:
        st.markdown("**🆕 Model v2 Features:**")
        st.info("""
        ✅ Target structure analysis
        ✅ Risk-reward ratio calculation
        ✅ Dynamic threshold adjustment
        ✅ Price recommendation output
        ✅ Calibrated probabilities
        ✅ Policy band system
        """)
        
        st.markdown("**📊 Performance:**")
        if ML_BUNDLE:
            st.success("""
            **Strict Accuracy:** 24.73%
            **Cumulative:** 49.76%
            **FP Non-hit:** 23.53%
            **Stage-C:** ~90%
            """)
        else:
            st.error("❌ Model v2 not available")

def render_ml_prediction(ml_result, settings):
    """Render ML prediction results"""
    if 'error' in ml_result:
        st.error(f"❌ ML Prediction Failed: {ml_result['error']}")
        return
    
    st.subheader("🤖 ML Model v2 Prediction")
    
    pred = ml_result['predicted_min_tp']
    confidence = ml_result.get('p_hit_stageA', 0)
    price_reco = ml_result.get('recommended_price')
    change_reco = ml_result.get('recommended_change_pct')
    
    if pred is not None:
        label = tp_label(pred)
        emoji = tp_emoji(pred)
        
        # Color coding
        if pred >= 3:
            card_color = COLORS['green']
        elif pred >= 1:
            card_color = COLORS['blue']
        elif pred == 0:
            card_color = COLORS['yellow']
        else:
            card_color = COLORS['red']
        
        # Build recommendation text
        reco_text = label
        if price_reco and change_reco:
            reco_text += f" (${price_reco:.4f}, {change_reco:+.2f}%)"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1A1D24 0%, #252831 100%);
            border: 3px solid {card_color};
            border-radius: 20px;
            padding: 30px;
            margin: 20px 0;
            text-align: center;
        ">
            <h1 style="color: {card_color}; margin: 0; font-size: 48px;">
                {emoji}
            </h1>
            <h2 style="color: {card_color}; margin: 10px 0;">
                🎯 Recommended: {reco_text}
            </h2>
            <p style="color: #A0A0A0; margin: 10px 0; font-size: 16px;">
                Stage-A Probability: {confidence:.1%}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Analysis details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔍 Model Analysis:**")
            
            base_th = ml_result.get('threshold_used_base', 0.32)
            go_hit = ml_result.get('go_hit_decision', False)
            
            st.metric("Stage-A Probability", f"{confidence:.3f}")
            st.metric("Base Threshold", f"{base_th:.3f}")
            
            if settings.get('show_technical_details'):
                band = ml_result.get('threshold_used_band', 0.08)
                eff_th = ml_result.get('threshold_used_effective', base_th)
                st.metric("Policy Band", f"{band:.3f}")
                st.metric("Effective Threshold", f"{eff_th:.3f}")
                st.metric("Final Decision", "HIT" if go_hit else "MISS")
            
            # Volume and risk info
            vol_rank = ml_result.get('volume_rank')
            if vol_rank and vol_rank[0] and vol_rank[1]:
                vol_score = 1 - (vol_rank[0] / vol_rank[1])
                st.metric("Volume Score", f"{vol_score:.3f}")
            
            if ml_result.get('risk_level'):
                st.metric("Risk Level", ml_result['risk_level'])
        
        with col2:
            st.markdown("**💡 Trading Recommendation:**")
            
            # Confidence warnings
            if confidence < base_th:
                st.error("⚠️ **Low Confidence Signal**")
                st.warning("Model suggests SKIP this trade")
            elif not go_hit:
                st.warning("⚠️ **Cautious Signal**")
                st.info("Model is uncertain - consider smaller position")
            else:
                if pred >= 3:
                    st.success("🚀 **Strong Buy Signal**")
                    st.write("✅ High probability for TP3+ achievement")
                    if price_reco:
                        st.write(f"🎯 Target price: ${price_reco:.4f}")
                elif pred >= 1:
                    st.info("📊 **Moderate Buy Signal**")
                    st.write(f"✅ Model predicts {label} achievement")
                    if price_reco:
                        st.write(f"🎯 Target price: ${price_reco:.4f}")
                else:
                    st.error("🔻 **Avoid Signal**")
                    st.write("❌ High risk of stop loss")
            
            # Risk profile adjustments
            if settings['risk_adjustment'] == 'Conservative' and pred >= 2:
                st.info("🛡️ Conservative: Consider taking profits at TP1-TP2")
            elif settings['risk_adjustment'] == 'Aggressive' and pred >= 1:
                st.info("🚀 Aggressive: Hold for higher targets")

def render_historical_analysis(pair, historical_data):
    """Render historical performance analysis"""
    if not historical_data:
        return
    
    st.subheader("📊 Historical Performance Analysis")
    
    # Metrics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Win Rate", f"{historical_data['overall_wr']:.1%}")
    with col2:
        st.metric("Total Trades", f"{historical_data['closed_trades']}")
    with col3:
        st.metric("TP3+ Success", f"{(historical_data['tp3_prob'] + historical_data['tp4_prob']):.1%}")
    with col4:
        st.metric("SL Rate", f"{historical_data['sl_prob']:.1%}")
    
    # Success rate chart
    tp_data = {
        'TP Level': ['TP1', 'TP2', 'TP3', 'TP4'],
        'Success Rate': [
            historical_data['tp1_prob'] * 100,
            historical_data['tp2_prob'] * 100,
            historical_data['tp3_prob'] * 100,
            historical_data['tp4_prob'] * 100
        ],
        'Count': [
            historical_data['tp1_hits'],
            historical_data['tp2_hits'],
            historical_data['tp3_hits'],
            historical_data['tp4_hits']
        ]
    }
    
    fig = go.Figure(data=[go.Bar(
        x=tp_data['TP Level'],
        y=tp_data['Success Rate'],
        marker_color=COLORS['blue'],
        text=[f"{rate:.1f}%<br>({count} hits)" for rate, count in zip(tp_data['Success Rate'], tp_data['Count'])],
        textposition='outside'
    )])
    
    fig.update_layout(
        title=f"Historical TP Success Rates - {pair}",
        yaxis_title="Success Rate (%)",
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def parse_trading_call_simple(call_text):
    """Simple parsing for compatibility"""
    parsed = parse_call_text(call_text)
    return {
        'pair': parsed.get('pair'),
        'entry': parsed.get('entry'),
        'targets': list(parsed.get('targets', {}).values()),
        'stops': list(parsed.get('stops', {}).values()),
        'risk_level': parsed.get('risk_level'),
        'volume_rank': parsed.get('volume_rank_num'),
        'volume_total': parsed.get('volume_rank_den')
    }

def main():
    """Main application function"""
    render_page_header()
    
    # Sidebar
    settings = render_prediction_sidebar()
    
    # Main content
    call_text, analyze_button = render_call_input()
    
    if analyze_button and call_text.strip():
        with st.spinner("Analyzing trading call..."):
            
            # Parse call
            parsed_call = parse_trading_call_simple(call_text)
            
            if parsed_call and parsed_call.get('pair'):
                st.success("✅ Call parsed successfully!")
                
                # ML Prediction
                if ML_BUNDLE:
                    with st.spinner("Running ML prediction..."):
                        ml_result = predict_min_tp_from_text(call_text, ML_BUNDLE)
                        render_ml_prediction(ml_result, settings)
                        st.markdown("---")
                else:
                    st.error("❌ ML Model not available")
                
                # Historical Analysis
                try:
                    with st.spinner(f"Loading historical data for {parsed_call['pair']}..."):
                        conn_status = get_connection_status()
                        if conn_status.get("connected"):
                            raw_data = load_data()
                            if raw_data and 'signals' in raw_data:
                                processed_data = process_signals(raw_data)
                                historical_data = get_historical_performance(parsed_call['pair'], processed_data)
                                
                                if historical_data:
                                    st.success(f"📈 Found {historical_data['total_signals']} historical signals")
                                    render_historical_analysis(parsed_call['pair'], historical_data)
                                else:
                                    st.info(f"ℹ️ No historical data found for {parsed_call['pair']}")
                            else:
                                st.info("ℹ️ No signal data available")
                        else:
                            st.info("ℹ️ Database not connected - ML prediction only")
                except Exception:
                    st.info("ℹ️ Historical analysis unavailable")
                
            else:
                st.error("❌ Failed to parse trading call")
    
    elif analyze_button:
        st.warning("⚠️ Please paste a trading call to analyze")
    
    # Footer
    st.markdown("---")
    with st.expander("Model v2 Architecture"):
        base_th = ML_BUNDLE.get('stageA_threshold', 0.32) if ML_BUNDLE else 0.32
        policy_band = ML_BUNDLE.get('policy_band', 0.08) if ML_BUNDLE else 0.08
        
        st.markdown(f"""
        ### Enhanced Two-Stage Pipeline v2
        
        **Key Improvements over v1:**
        
        **Architecture:**
        - Stage-A: Isotonic calibrated TP≥1 probability
        - Stage-B: Class-weighted TP level (1-4) prediction
        - Stage-C: Binary SL vs No-outcome for misses
        
        **Enhanced Features:**
        - Target percentages (tp1_pct, tp2_pct, tp3_pct, tp4_pct)
        - Stop loss percentages (sl1_pct, sl2_pct)
        - Risk-reward ratios (RR1, RR2, RR3, RR4)
        - Target spacing, tightness, summary statistics
        - Volume rank score, risk numeric encoding
        
        **Dynamic Thresholding:**
        - Base threshold: {base_th:.3f}
        - Policy band: {policy_band:.3f}
        - Effective adjustment based on volume/risk/TP1 distance
        
        **Performance Metrics:**
        - Strict accuracy: 24.73% (vs ~22-26% v1)
        - Cumulative: 49.76% (maintained ~49%)
        - False positive non-hit: 23.53% (reduced from ~24.5%)
        - Stage-C accuracy: ~90% (stable)
        
        **Outputs:**
        - Recommended price from parsed targets
        - Percentage change from entry
        - Calibrated probability scores
        - Dynamic threshold breakdown
        - Historical performance comparison
        """)

if __name__ == "__main__":
    main()
"""
🔮 Call Prediction - LuxQuant Pro v2 (Optimal Version)
AI-powered analysis and recommendations for trading calls
Enhanced with robust error handling and graceful degradation
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

# Enhanced Model Loading with Robust Error Handling
ML_BUNDLE = None
ML_ERROR_MESSAGE = ""
ML_STATUS = "loading"

@st.cache_resource
def load_ml_model_safe():
    """
    Safe ML model loading with comprehensive error handling
    Returns (model, status, error_message)
    """
    try:
        from joblib import load
        
        # Possible model file locations
        model_paths = [
            "luxquant_tp_twostage_bundle.joblib",
            "luxquant_tp_twostagенew_bundle.joblib",
            "models/luxquant_tp_twostage_bundle.joblib",
            "assets/luxquant_tp_twostage_bundle.joblib",
            "./luxquant_tp_twostage_bundle.joblib"
        ]
        
        for path in model_paths:
            try:
                if os.path.exists(path):
                    bundle = load(path)
                    
                    # Validate model structure
                    required_keys = ['pipe_A', 'pipe_B', 'pipe_C', 'num_cols', 'cat_cols']
                    if all(key in bundle for key in required_keys):
                        return bundle, "loaded", f"Model loaded from: {path}"
                    else:
                        continue
                        
            except FileNotFoundError:
                continue
            except Exception as e:
                error_msg = str(e)
                if any(term in error_msg.lower() for term in ['sklearn', 'version', 'attribute', 'module']):
                    # Try compatibility fix for sklearn version issues
                    try:
                        import importlib
                        import sklearn.compose._column_transformer
                        importlib.reload(sklearn.compose._column_transformer)
                        bundle = load(path)
                        return bundle, "loaded_compat", f"Model loaded (compatibility mode): {path}"
                    except:
                        continue
                else:
                    continue
        
        return None, "not_found", "Model file not found in any expected location"
        
    except ImportError:
        return None, "no_joblib", "joblib library not available"
    except Exception as e:
        return None, "error", f"Unexpected error: {str(e)}"

# Initialize ML model
ML_BUNDLE, ML_STATUS, ML_ERROR_MESSAGE = load_ml_model_safe()

# Import modules with error handling
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.connection import get_connection_status, load_data
    from data_processing.signal_processor import process_signals
    from config.theme import COLORS, CUSTOM_CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
except ImportError:
    # Fallback colors if theme import fails
    COLORS = {
        "green": "#00D46A",
        "red": "#FF4747", 
        "blue": "#4B9BFF",
        "yellow": "#FDB32B",
        "purple": "#9D5CFF",
        "background": "#0E1117"
    }

# Enhanced Text Parsing Patterns
PAIR_PAT = re.compile(r"NEW\s*CALL:\s*([A-Z0-9_]+USDT)", re.IGNORECASE)
VOL_PAT = re.compile(r"Volume\(24H\)\s*Ranked:\s*(?:🏅\s*)?(\d+)(?:st|nd|rd|th)?/(\d+)", re.IGNORECASE)
RISK_PAT = re.compile(r"Risk\s*Level\s*[:\-]?\s*(?:⚠️\s*)?([A-Za-z]+)", re.IGNORECASE)
ENTRY_PAT = re.compile(r"Entry\s*:\s*([0-9]+(?:[\.,][0-9]+)?)", re.IGNORECASE)

def parse_call_text(call_text: str):
    """Enhanced trading call text parsing with better error handling"""
    try:
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
            if any(term in raw for term in ["high", "tinggi", "red"]):
                risk = "High"
            elif any(term in raw for term in ["medium", "mid", "yellow"]):
                risk = "Medium"
            elif any(term in raw for term in ["low", "rendah", "green", "normal"]):
                risk = "Low"

        # Extract targets with enhanced patterns
        target_patterns = [
            r'Target\s*1\s*:?\s*([0-9]+(?:[\.,][0-9]+)?)',
            r'Target\s*2\s*:?\s*([0-9]+(?:[\.,][0-9]+)?)',
            r'Target\s*3\s*:?\s*([0-9]+(?:[\.,][0-9]+)?)',
            r'Target\s*4\s*:?\s*([0-9]+(?:[\.,][0-9]+)?)'
        ]
        
        targets = {}
        for i, pattern in enumerate(target_patterns, 1):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                targets[i] = float(match.group(1).replace(',', '.'))

        # Extract stops
        stop_patterns = [
            r'Stop\s*Loss\s*1\s*:?\s*([0-9]+(?:[\.,][0-9]+)?)',
            r'Stop\s*Loss\s*2\s*:?\s*([0-9]+(?:[\.,][0-9]+)?)'
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
            "stops": stops,
            "parsing_success": True
        }
        
    except Exception as e:
        return {
            "pair": None,
            "entry": None,
            "volume_rank_num": None,
            "volume_rank_den": None,
            "risk_level": None,
            "targets": {},
            "stops": {},
            "parsing_success": False,
            "parsing_error": str(e)
        }

def build_feature_row_from_text(parsed: dict, num_cols, cat_cols):
    """Build feature row for ML model with enhanced validation"""
    try:
        if not parsed.get('parsing_success', False):
            return pd.DataFrame(), {}
        
        # Basic features with safe calculations
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
            if i in targets and entry and not np.isnan(entry) and entry > 0:
                row[f"tp{i}_pct"] = ((targets[i] - entry) / entry) * 100
            else:
                row[f"tp{i}_pct"] = np.nan

        # Stop loss percentage features
        for i in range(1, 3):
            if i in stops and entry and not np.isnan(entry) and entry > 0:
                row[f"sl{i}_pct"] = ((stops[i] - entry) / entry) * 100
            else:
                row[f"sl{i}_pct"] = np.nan

        # Risk-Reward ratios
        sl1 = stops.get(1)
        if sl1 and entry and not np.isnan(entry) and entry > 0:
            risk_amount = abs(entry - sl1)
            for i in range(1, 5):
                if i in targets and risk_amount > 0:
                    reward_amount = abs(targets[i] - entry)
                    row[f"RR{i}"] = reward_amount / risk_amount
                else:
                    row[f"RR{i}"] = np.nan
        else:
            for i in range(1, 5):
                row[f"RR{i}"] = np.nan

        # Target spacing features
        valid_targets = [targets[i] for i in sorted(targets.keys()) if i in targets]
        if len(valid_targets) >= 2 and entry and not np.isnan(entry) and entry > 0:
            spacings = [valid_targets[i] - valid_targets[i-1] for i in range(1, len(valid_targets))]
            row["spacing"] = np.mean(spacings) / entry
            row["tightness"] = np.std(spacings) / entry if len(spacings) > 1 else np.nan
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
        
    except Exception as e:
        return pd.DataFrame(), {}

def eff_threshold(X_row, base=0.32):
    """Calculate effective threshold with safe error handling"""
    try:
        if X_row.empty:
            return base
            
        volume_rank_score = X_row.iloc[0].get('volume_rank_score', 0.5)
        risk_num = X_row.iloc[0].get('risk_num', 1)
        tp1_pct = X_row.iloc[0].get('tp1_pct', 5)
        
        threshold_adj = 0
        
        # Volume adjustment
        if not np.isnan(volume_rank_score) and volume_rank_score < 0.3:
            threshold_adj += 0.05
        
        # Risk adjustment
        if not np.isnan(risk_num) and risk_num >= 2:
            threshold_adj += 0.03
        
        # TP1 adjustment
        if not np.isnan(tp1_pct) and tp1_pct < 2:
            threshold_adj += 0.04
        
        return base + threshold_adj
    except:
        return base

def predict_min_tp_from_text(call_text: str, bundle: dict):
    """Enhanced ML prediction with comprehensive error handling"""
    if bundle is None:
        return {
            "error": "ML model not loaded",
            "predicted_min_tp": None,
            "confidence": 0
        }
    
    try:
        parsed = parse_call_text(call_text)
        
        if not parsed.get('parsing_success', False):
            return {
                "error": f"Call parsing failed: {parsed.get('parsing_error', 'Unknown parsing error')}",
                "predicted_min_tp": None,
                "confidence": 0
            }
        
        X_row, targets = build_feature_row_from_text(parsed, bundle["num_cols"], bundle["cat_cols"])
        
        if X_row.empty:
            return {
                "error": "Feature extraction failed",
                "predicted_min_tp": None,
                "confidence": 0
            }
        
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
            "go_hit_decision": go_hit,
            "prediction_success": True
        }
    
    except Exception as e:
        return {
            "error": f"Prediction failed: {str(e)}",
            "predicted_min_tp": None,
            "confidence": 0,
            "prediction_success": False
        }

def get_historical_performance(pair, data):
    """Get historical performance data with error handling"""
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
    """Render sidebar controls with ML status"""
    st.sidebar.title("🔮 AI Prediction v2")
    
    # Enhanced ML status display
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
            st.sidebar.caption("Model details loaded")
    else:
        st.sidebar.error("❌ ML Model v2: NOT LOADED")
        st.sidebar.warning(f"Status: {ML_STATUS}")
        st.sidebar.info(f"Details: {ML_ERROR_MESSAGE}")
        
        # Show what's available without ML
        st.sidebar.markdown("""
        **🔧 Available Features:**
        - ✅ Call text parsing
        - ✅ Historical analysis
        - ✅ Database connectivity
        - ✅ Performance metrics
        
        **❌ Unavailable:**
        - ❌ ML predictions
        - ❌ Price recommendations
        """)
    
    # Model features info
    st.sidebar.markdown("""
    **Model v2 Features:**
    - Two-stage calibrated pipeline
    - Target structure analysis
    - Dynamic threshold adjustment
    - Price recommendation output
    """)
    
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
        if ML_BUNDLE:
            st.success("""
            ✅ Target structure analysis
            ✅ Risk-reward ratio calculation
            ✅ Dynamic threshold adjustment
            ✅ Price recommendation output
            ✅ Calibrated probabilities
            ✅ Policy band system
            """)
            
            st.markdown("**📊 Performance:**")
            st.success("""
            **Strict Accuracy:** 24.73%
            **Cumulative:** 49.76%
            **FP Non-hit:** 23.53%
            **Stage-C:** ~90%
            """)
        else:
            st.error("""
            ❌ ML Model not available
            
            **Available:**
            ✅ Call text parsing
            ✅ Historical analysis
            ✅ Database connectivity
            
            **Reason:** """ + ML_ERROR_MESSAGE)

def render_ml_prediction(ml_result, settings):
    """Render ML prediction results with enhanced error handling"""
    if not ml_result.get('prediction_success', False):
        st.error(f"❌ ML Prediction Failed: {ml_result.get('error', 'Unknown error')}")
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
            
            # Enhanced confidence analysis
            if confidence < base_th:
                st.error("⚠️ **Low Confidence Signal**")
                st.warning("Model suggests SKIP this trade")
                st.info("🔍 Consider waiting for higher confidence signals")
            elif not go_hit:
                st.warning("⚠️ **Cautious Signal**")
                st.info("Model is uncertain - consider smaller position")
                st.info("📊 Monitor for confirmation signals")
            else:
                if pred >= 3:
                    st.success("🚀 **Strong Buy Signal**")
                    st.write("✅ High probability for TP3+ achievement")
                    if price_reco:
                        st.write(f"🎯 Target price: ${price_reco:.4f}")
                        st.write(f"📈 Expected gain: {change_reco:+.2f}%")
                elif pred >= 1:
                    st.info("📊 **Moderate Buy Signal**")
                    st.write(f"✅ Model predicts {label} achievement")
                    if price_reco:
                        st.write(f"🎯 Target price: ${price_reco:.4f}")
                        st.write(f"📈 Expected gain: {change_reco:+.2f}%")
                else:
                    st.error("🔻 **Avoid Signal**")
                    st.write("❌ High risk of stop loss")
                    st.write("🛡️ Consider risk management")
            
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
    """Simple parsing for compatibility with graceful error handling"""
    try:
        parsed = parse_call_text(call_text)
        return {
            'pair': parsed.get('pair'),
            'entry': parsed.get('entry'),
            'targets': list(parsed.get('targets', {}).values()),
            'stops': list(parsed.get('stops', {}).values()),
            'risk_level': parsed.get('risk_level'),
            'volume_rank': parsed.get('volume_rank_num'),
            'volume_total': parsed.get('volume_rank_den'),
            'parsing_success': parsed.get('parsing_success', False)
        }
    except Exception as e:
        return {
            'pair': None,
            'entry': None,
            'targets': [],
            'stops': [],
            'risk_level': None,
            'volume_rank': None,
            'volume_total': None,
            'parsing_success': False,
            'error': str(e)
        }

def render_parsing_results(parsed_call):
    """Render parsing results with enhanced display"""
    if not parsed_call.get('parsing_success', False):
        st.error("❌ Failed to parse trading call")
        if 'error' in parsed_call:
            st.error(f"Error: {parsed_call['error']}")
        return False
    
    st.success("✅ Call parsed successfully!")
    
    # Create enhanced display of parsed information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Basic Information:**")
        st.info(f"**Pair:** {parsed_call['pair'] or 'Not found'}")
        st.info(f"**Entry:** ${parsed_call['entry']:.4f}" if parsed_call['entry'] else "**Entry:** Not found")
        st.info(f"**Risk Level:** {parsed_call['risk_level'] or 'Not specified'}")
        
    with col2:
        st.markdown("**📈 Volume Analysis:**")
        if parsed_call['volume_rank'] and parsed_call['volume_total']:
            vol_score = 1 - (parsed_call['volume_rank'] / parsed_call['volume_total'])
            st.info(f"**Rank:** {parsed_call['volume_rank']}/{parsed_call['volume_total']}")
            st.info(f"**Score:** {vol_score:.3f}")
        else:
            st.info("**Volume:** Not specified")
        
    with col3:
        st.markdown("**🎯 Targets & Stops:**")
        targets = parsed_call.get('targets', [])
        stops = parsed_call.get('stops', [])
        st.info(f"**Targets:** {len(targets)} levels")
        st.info(f"**Stops:** {len(stops)} levels")
        
        if targets:
            st.info(f"**Range:** ${min(targets):.4f} - ${max(targets):.4f}")
    
    # Show target breakdown if available
    if targets:
        st.markdown("**🎯 Target Breakdown:**")
        target_df = pd.DataFrame({
            'Level': [f'TP{i+1}' for i in range(len(targets))],
            'Price': [f'${price:.4f}' for price in targets],
            'Change %': [f'{((price - parsed_call["entry"]) / parsed_call["entry"] * 100):+.2f}%' 
                        for price in targets] if parsed_call['entry'] else ['N/A'] * len(targets)
        })
        st.dataframe(target_df, use_container_width=True, hide_index=True)
    
    return True

def render_ml_unavailable_message():
    """Render informative message when ML is unavailable"""
    st.warning("🤖 ML Prediction Currently Unavailable")
    
    # Create informative status card
    status_color = {
        "not_found": "#FFA500",
        "no_joblib": "#FF6B6B", 
        "error": "#FF4747",
        "loading": "#4B9BFF"
    }.get(ML_STATUS, "#888888")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A1D24 0%, #252831 100%);
        border: 2px solid {status_color};
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        text-align: center;
    ">
        <h3 style="color: {status_color}; margin: 0;">
            🔧 ML Model Status: {ML_STATUS.replace('_', ' ').title()}
        </h3>
        <p style="color: #A0A0A0; margin: 15px 0;">
            {ML_ERROR_MESSAGE}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show what's available
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**✅ Available Features:**")
        st.success("""
        - 📝 Complete call text parsing
        - 📊 Historical performance analysis
        - 🎯 Target & stop loss extraction
        - 📈 Risk-reward calculations
        - 💾 Database connectivity
        - 📋 Performance metrics
        """)
    
    with col2:
        st.markdown("**❌ Unavailable Features:**")
        st.error("""
        - 🤖 AI prediction model
        - 🎯 Price recommendations
        - 📊 Confidence scoring
        - 🔮 ML-based analysis
        - 📈 Dynamic thresholding
        """)
    
    # Troubleshooting guide
    with st.expander("🔧 Troubleshooting Guide"):
        st.markdown(f"""
        ### Current Status: {ML_STATUS}
        
        **Possible Solutions:**
        
        1. **Model File Missing**: Upload `luxquant_tp_twostage_bundle.joblib` to repository root
        2. **Library Issues**: Check if joblib and scikit-learn are properly installed
        3. **Version Compatibility**: Ensure sklearn version matches model training version
        4. **File Path**: Verify model file is in correct location
        
        **For Developers:**
        ```bash
        # Check if model file exists
        ls -la luxquant_tp_twostage_bundle.joblib
        
        # Verify Python packages
        pip list | grep -E "(joblib|scikit-learn)"
        
        # Test model loading
        python -c "from joblib import load; load('luxquant_tp_twostage_bundle.joblib')"
        ```
        
        **Current Error Details:**
        ```
        Status: {ML_STATUS}
        Message: {ML_ERROR_MESSAGE}
        ```
        """)

def main():
    """Enhanced main application function with comprehensive error handling"""
    render_page_header()
    
    # Sidebar with ML status
    settings = render_prediction_sidebar()
    
    # Main content
    call_text, analyze_button = render_call_input()
    
    if analyze_button and call_text.strip():
        with st.spinner("🔍 Analyzing trading call..."):
            
            # Parse call (this always works)
            parsed_call = parse_trading_call_simple(call_text)
            
            # Display parsing results
            if render_parsing_results(parsed_call):
                
                st.markdown("---")
                
                # ML Prediction Section
                if ML_BUNDLE:
                    with st.spinner("🤖 Running ML prediction..."):
                        ml_result = predict_min_tp_from_text(call_text, ML_BUNDLE)
                        render_ml_prediction(ml_result, settings)
                else:
                    render_ml_unavailable_message()
                
                st.markdown("---")
                
                # Historical Analysis (always available if database works)
                if parsed_call.get('pair'):
                    try:
                        with st.spinner(f"📊 Loading historical data for {parsed_call['pair']}..."):
                            conn_status = get_connection_status()
                            
                            if conn_status.get("connected"):
                                raw_data = load_data()
                                if raw_data and 'signals' in raw_data:
                                    processed_data = process_signals(raw_data)
                                    historical_data = get_historical_performance(parsed_call['pair'], processed_data)
                                    
                                    if historical_data and historical_data['closed_trades'] > 0:
                                        st.success(f"📈 Found {historical_data['total_signals']} historical signals for {parsed_call['pair']}")
                                        render_historical_analysis(parsed_call['pair'], historical_data)
                                    else:
                                        st.info(f"ℹ️ No historical performance data found for {parsed_call['pair']}")
                                        st.info("This might be a new pair or no closed trades available")
                                else:
                                    st.warning("⚠️ No signal data available in database")
                            else:
                                st.warning("⚠️ Database not connected")
                                st.info("Historical analysis requires database connectivity")
                                if 'error' in conn_status:
                                    st.error(f"Database error: {conn_status['error']}")
                                    
                    except Exception as e:
                        st.warning(f"⚠️ Historical analysis failed: {str(e)}")
                        st.info("Analysis will continue with available features")
                
                # Additional Analysis Section
                st.markdown("---")
                render_additional_analysis(parsed_call)
                
            else:
                # Parsing failed, show help
                st.markdown("---")
                render_parsing_help()
    
    elif analyze_button:
        st.warning("⚠️ Please paste a trading call to analyze")
    
    # Footer with model information
    render_footer()

def render_additional_analysis(parsed_call):
    """Render additional analysis that doesn't require ML"""
    st.subheader("📊 Additional Analysis")
    
    if not parsed_call.get('parsing_success'):
        st.info("Additional analysis requires successful call parsing")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💹 Risk-Reward Analysis**")
        
        entry = parsed_call.get('entry')
        targets = parsed_call.get('targets', [])
        stops = parsed_call.get('stops', [])
        
        if entry and targets and stops:
            # Calculate RR ratios
            risk = abs(entry - stops[0]) if stops else 0
            
            if risk > 0:
                rr_ratios = []
                for i, target in enumerate(targets, 1):
                    reward = abs(target - entry)
                    rr = reward / risk
                    rr_ratios.append((f'TP{i}', rr))
                    st.info(f"**TP{i} RR:** {rr:.2f}")
                
                # Best RR
                if rr_ratios:
                    best_rr = max(rr_ratios, key=lambda x: x[1])
                    st.success(f"**Best RR:** {best_rr[0]} = {best_rr[1]:.2f}")
            else:
                st.warning("Cannot calculate RR - no stop loss data")
        else:
            st.warning("Insufficient data for RR analysis")
    
    with col2:
        st.markdown("**📈 Price Movement Analysis**")
        
        if entry and targets:
            # Calculate percentage movements
            movements = []
            for i, target in enumerate(targets, 1):
                pct_change = ((target - entry) / entry) * 100
                movements.append((f'TP{i}', pct_change))
                
                color = "🟢" if pct_change > 0 else "🔴"
                st.info(f"**TP{i}:** {color} {pct_change:+.2f}%")
            
            # Total potential
            if movements:
                total_potential = movements[-1][1]  # Highest target
                st.success(f"**Total Potential:** {total_potential:+.2f}%")
        else:
            st.warning("Insufficient data for movement analysis")

def render_parsing_help():
    """Render help for parsing issues"""
    st.subheader("📝 Parsing Help")
    
    st.error("❌ Unable to parse the trading call")
    
    st.markdown("**✅ Expected Format:**")
    st.code("""
🆕 NEW CALL: BTCUSDT 🆕

📊 Risk Analysis 📊
Volume(24H) Ranked: 15th/517
Risk Level: 🟢 Normal

**Entry: 45000**

📝 Targets & Stop Loss
Target 1: 46000
Target 2: 47000  
Target 3: 48000
Target 4: 50000
Stop Loss 1: 44000
Stop Loss 2: 43000
    """)
    
    st.markdown("**🔍 Common Issues:**")
    st.warning("""
    - Missing pair name (should be like BTCUSDT, ETHUSDT)
    - Missing entry price
    - Targets not clearly labeled
    - Invalid number formats
    """)
    
    st.markdown("**💡 Tips:**")
    st.info("""
    - Ensure pair name ends with USDT
    - Use clear "Entry:", "Target 1:", etc. labels
    - Include risk level and volume ranking if available
    - Use standard number formats (decimals with dots)
    """)

def render_footer():
    """Render footer with model and app information"""
    st.markdown("---")
    
    with st.expander("ℹ️ Model & App Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🤖 ML Model v2 Architecture")
            if ML_BUNDLE:
                st.success("**Status:** Loaded ✅")
                try:
                    base_th = ML_BUNDLE.get('stageA_threshold', 0.32)
                    policy_band = ML_BUNDLE.get('policy_band', 0.08)
                    
                    st.markdown(f"""
                    **Model Configuration:**
                    - Base threshold: {base_th:.3f}
                    - Policy band: {policy_band:.3f}
                    - Features: {len(ML_BUNDLE.get('num_cols', [])) + len(ML_BUNDLE.get('cat_cols', []))}
                    
                    **Pipeline Stages:**
                    - Stage A: TP≥1 probability (calibrated)
                    - Stage B: TP level prediction (1-4)
                    - Stage C: SL vs No-outcome classification
                    """)
                except:
                    st.info("Model loaded but details unavailable")
            else:
                st.error(f"**Status:** {ML_STATUS} ❌")
                st.info(f"**Details:** {ML_ERROR_MESSAGE}")
        
        with col2:
            st.markdown("### 📊 App Features")
            st.markdown("""
            **✅ Always Available:**
            - Complete call text parsing
            - Historical performance analysis
            - Target & stop extraction
            - Risk-reward calculations
            - Database connectivity
            - Performance metrics
            
            **🤖 ML-Dependent:**
            - AI prediction model
            - Price recommendations  
            - Confidence scoring
            - Dynamic thresholding
            
            **📈 Performance Metrics:**
            - Strict accuracy: 24.73%
            - Cumulative: 49.76%
            - Stage-C accuracy: ~90%
            """)

if __name__ == "__main__":
    main()

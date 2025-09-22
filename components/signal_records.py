# components/signal_record.py
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def build_signal_record(signals: pd.DataFrame) -> pd.DataFrame:
    """
    Kembalikan DataFrame tanpa kolom target/stop.
    Dipanggil hanya saat tab 'Signal Record' aktif.
    """
    if signals is None or signals.empty:
        return pd.DataFrame()

    # drop kolom target*/stop* (case-insensitive, fleksibel)
    drop_prefixes = ("target", "stop")
    keep_cols = [c for c in signals.columns
                 if not c.lower().startswith(drop_prefixes)]
    df = signals.loc[:, keep_cols].copy()

    # opsional: urutkan terbaru di atas jika ada 'created_at'
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df = df.sort_values("created_at", ascending=False)

    return df

def render_signal_record(signals: pd.DataFrame):
    df = build_signal_record(signals)
    if df.empty:
        st.info("Tidak ada data untuk ditampilkan.")
        return
    st.subheader("Complete Dataset — Signal Record")
    st.dataframe(df, use_container_width=True)

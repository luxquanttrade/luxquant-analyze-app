"""
Database connection and data loading logic
"""
import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from config.settings import TABLE_MAPPINGS

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

def get_connection_string():
    """Get database connection string from secrets atau ENV; fallback terakhir ke localhost:5433."""
    # 1) Streamlit secrets (jika kamu pakai .streamlit/secrets.toml)
    try:
        url = st.secrets["database"]["connection_url"]
        if url:
            return url
    except Exception:
        pass

    # 2) ENV (diset di systemd)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # 3) Fallback lokal (VPS yang sama). Boleh pertahankan sebagai cadangan.
    return "postgresql://luxq:ukCjpVAkqpeExAiLcFNETgmP@127.0.0.1:5433/luxquant"


def get_connection_status():
    """Check database connection status"""
    if not POSTGRES_AVAILABLE:
        return {
            'connected': False, 
            'error': 'Missing PostgreSQL dependencies. Run: pip install psycopg2-binary sqlalchemy'
        }
    
    connection_string = get_connection_string()
    if not connection_string:
        return {
            'connected': False,
            'error': 'No connection string configured'
        }
    
    # Test actual connection through SSH tunnel
    try:
        from sqlalchemy import create_engine
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
        
        return {
            'connected': True,
            'connection_string': connection_string,
            'test_result': 'Connection successful'
        }
    except Exception as e:
        return {
            'connected': False,
            'error': f'Connection failed: {str(e)}',
            'connection_string': connection_string  # Include for debugging
        }

@st.cache_data(show_spinner=False, ttl=10)  # Cache only for 10 seconds during debug
def load_data():
    """Load data from database"""
    connection_status = get_connection_status()
    
    if not connection_status['connected']:
        st.error(connection_status['error'])
        return None
    
    try:
        engine = create_engine(connection_status['connection_string'])
        result = {"__tables__": []}
        
        # Get table names
        with engine.connect() as conn:
            tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """)
            tables_result = conn.execute(tables_query)
            table_names = [row[0] for row in tables_result]
            result["__tables__"] = table_names

        # Load tables based on mappings
        for key, possible_names in TABLE_MAPPINGS.items():
            for table_name in possible_names:
                if table_name in table_names:
                    try:
                        df = pd.read_sql_table(table_name, engine)
                        result[key] = df
                        break
                    except Exception as e:
                        st.warning(f"Could not load table {table_name}: {e}")
                        continue

        return result
        
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def safe_read_table(table_name, engine):
    """Safely read a database table"""
    try:
        return pd.read_sql_table(table_name, engine)
    except Exception as e:
        st.warning(f"Could not load table {table_name}: {e}")
        return None
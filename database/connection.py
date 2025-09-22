"""
Database connection and data loading logic — Streamlit Cloud Ready
VPS Setup: PostgreSQL 12 on port 5433 with SSL enabled
Updated to match test connection configuration
"""
import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config.settings import TABLE_MAPPINGS

try:
    import psycopg2  # noqa: F401
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

def get_connection_string():
    """
    Ambil connection URL dari Streamlit Secrets atau ENV.
    Format sesuai dengan test connection yang sudah berhasil.
    """
    # 1) Streamlit secrets (priority untuk Cloud deployment)
    try:
        url = st.secrets["database"]["connection_url"]
        if url and url.strip():
            return url.strip()
    except Exception:
        pass
    
    # 2) Individual components dari secrets (alternative method)
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            db_config = st.secrets['database']
            if all(key in db_config for key in ['host', 'port', 'database', 'username', 'password']):
                host = db_config['host']
                port = db_config['port']
                database = db_config['database']
                username = db_config['username']
                password = db_config['password']
                
                # URL-encode password untuk handling karakter spesial
                pwd_enc = quote_plus(str(password))
                return f"postgresql+psycopg2://{username}:{pwd_enc}@{host}:{port}/{database}?sslmode=require"
    except Exception:
        pass

    # 3) ENV (untuk dev lokal)
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        return db_url.strip()

    # 4) Tidak dikonfigurasi - tidak ada fallback localhost untuk Cloud
    return None

def make_engine(conn_str: str):
    """
    Factory SQLAlchemy Engine dengan setelan yang sama seperti test connection.
    Menggunakan konfigurasi yang telah terbukti berhasil.
    """
    return create_engine(
        conn_str,
        pool_size=1,
        max_overflow=0,
        pool_timeout=30,
        pool_recycle=3600,
        connect_args={"sslmode": "require", "connect_timeout": 10},
    )

def get_connection_status():
    """
    Cek koneksi DB dengan test yang sama seperti di test script.
    Memberikan informasi detail tentang koneksi.
    """
    if not POSTGRES_AVAILABLE:
        return {
            "connected": False,
            "error": "Missing PostgreSQL deps. Install: psycopg2-binary, sqlalchemy",
        }

    conn_str = get_connection_string()
    if not conn_str:
        return {
            "connected": False,
            "error": "No DB connection configured. Set [database].connection_url in Streamlit secrets atau DATABASE_URL env.",
        }

    try:
        engine = make_engine(conn_str)
        with engine.connect() as conn:
            # Test query yang sama seperti di test script
            result = conn.execute(text("SELECT current_user, inet_client_addr(), version(), now()"))
            row = result.fetchone()
            
            if row:
                current_user = row[0]
                client_addr = row[1] 
                version_info = row[2].splitlines()[0] if row[2] else "Unknown"
                server_time = row[3]
                
                return {
                    "connected": True, 
                    "connection_string": mask_connection_string(conn_str), 
                    "test_result": "Connection successful",
                    "current_user": current_user,
                    "client_addr": str(client_addr) if client_addr else "Unknown",
                    "server_version": version_info,
                    "server_time": str(server_time),
                    "ssl_enabled": True
                }
            else:
                return {
                    "connected": False,
                    "error": "Connection test query returned no data"
                }
        
    except Exception as e:
        msg = str(e).lower()
        hint = None
        if "timeout" in msg:
            hint = "Timeout. Cek ufw allow 5433 dan pg_hba.conf di VPS."
        elif "ssl" in msg:
            hint = "SSL issue. Pastikan sslmode=require & server Postgres ssl=on."
        elif "password" in msg or "authentication" in msg:
            hint = "Auth gagal. Cek username/password secrets. Password: 'PasswordReaderKuat!'"
        elif "could not translate host name" in msg or "host" in msg:
            hint = "Host tidak bisa di-resolve. Pastikan IP VPS benar: 141.11.25.194"
        elif "connection refused" in msg:
            hint = "Connection refused. Cek PostgreSQL running di port 5433 dan firewall."
        elif "role" in msg and "does not exist" in msg:
            hint = "User luxq_readonly belum dibuat. Jalankan CREATE USER di VPS."
        
        return {
            "connected": False, 
            "error": f"DB connect failed: {e}", 
            "hint": hint,
            "connection_string": mask_connection_string(conn_str)
        }

def mask_connection_string(conn_str):
    """Mask password dalam connection string untuk keamanan logging."""
    if not conn_str:
        return "None"
    
    try:
        # Hide password: postgresql://user:password@host:port/db
        if '://' in conn_str and '@' in conn_str:
            protocol_part = conn_str.split('://')[0]
            remainder = conn_str.split('://')[1]
            
            if '@' in remainder:
                user_pass_part = remainder.split('@')[0]
                host_db_part = remainder.split('@')[1]
                
                if ':' in user_pass_part:
                    user = user_pass_part.split(':')[0]
                    return f"{protocol_part}://{user}:***@{host_db_part}"
                else:
                    return f"{protocol_part}://{user_pass_part}@{host_db_part}"
        
        return conn_str[:30] + "***"
    except:
        return "***masked***"

@st.cache_data(show_spinner=False, ttl=300)  # Cache 5 menit untuk Cloud
def load_data():
    """Muat data dari DB (cache 5 menit untuk Cloud)."""
    status = get_connection_status()
    if not status["connected"]:
        st.error(f"❌ Database Error: {status['error']}")
        if status.get("hint"):
            st.info(f"💡 Hint: {status['hint']}")
        return None

    try:
        engine = make_engine(get_connection_string())
        result = {"__tables__": [], "__metadata__": {"loaded_at": pd.Timestamp.now()}}

        # Daftar tabel public
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
        table_names = [r[0] for r in rows]
        result["__tables__"] = table_names

        # Muat tabel sesuai mapping
        tables_loaded = 0
        for key, candidates in TABLE_MAPPINGS.items():
            for tbl in candidates:
                if tbl in table_names:
                    try:
                        df = pd.read_sql_table(tbl, engine)
                        result[key] = df
                        tables_loaded += 1
                        st.success(f"✅ Loaded '{tbl}' as '{key}': {len(df)} rows")
                        break
                    except Exception as e:
                        st.warning(f"⚠️ Could not load table {tbl}: {e}")
                        continue

        result["__metadata__"]["tables_loaded"] = tables_loaded
        
        if tables_loaded == 0:
            st.warning("⚠️ No tables were loaded successfully")

        return result

    except Exception as e:
        st.error(f"❌ Database loading failed: {e}")
        return None

def safe_read_table(table_name, engine):
    """Helper aman untuk baca satu tabel."""
    try:
        return pd.read_sql_table(table_name, engine)
    except Exception as e:
        st.warning(f"Could not load table {table_name}: {e}")
        return None

# Debug function untuk troubleshooting deployment
def debug_connection_info():
    """Show connection debug information untuk troubleshooting."""
    st.subheader("🔍 Connection Debug Info")
    
    # Environment detection
    is_cloud = (
        os.getenv('STREAMLIT_SHARING') or 
        os.getenv('STREAMLIT_CLOUD') or
        'streamlit.io' in os.getenv('HOSTNAME', '')
    )
    st.info(f"**Environment:** {'Streamlit Cloud ☁️' if is_cloud else 'Local/VPS 🖥️'}")
    
    # Connection string info (masked)
    conn_str = get_connection_string()
    if conn_str:
        st.info(f"**Connection:** {mask_connection_string(conn_str)}")
        
        # Show if SSL is required
        if 'sslmode=require' in conn_str:
            st.success("✅ SSL mode: require (secure)")
        elif 'ssl' in conn_str:
            st.info("ℹ️ SSL mode: detected in connection string")
        else:
            st.warning("⚠️ SSL mode: not specified")
    else:
        st.error("❌ No connection string configured")
        return
    
    # Secrets availability
    try:
        has_secrets = hasattr(st, 'secrets') and 'database' in st.secrets
        if has_secrets:
            st.success("✅ Streamlit Secrets: Available")
            # Check if it's the readonly user
            if 'luxq_readonly' in conn_str:
                st.info("🔒 Using readonly user (recommended)")
        else:
            st.error("❌ Streamlit Secrets: Not Found")
    except Exception as e:
        st.error(f"❌ Streamlit Secrets: Error accessing - {e}")
    
    # Connection test
    with st.spinner("Testing database connection..."):
        status = get_connection_status()
    
    if status['connected']:
        st.success("✅ Database connection successful!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", "Connected ✅")
            if 'server_info' in status:
                st.info(f"**Server:** {status['server_info']}")
        
        with col2:
            if status.get('ssl_enabled'):
                st.metric("SSL", "Enabled ✅")
            st.info("**Port:** 5433 (Custom)")
        
        # Test data loading
        with st.spinner("Testing data loading..."):
            try:
                data = load_data()
                if data and '__tables__' in data:
                    st.success(f"✅ Data loading successful!")
                    tables = data['__tables__']
                    st.info(f"**Available tables:** {', '.join(tables) if tables else 'None'}")
                    
                    # Show loaded data summary
                    if 'signals' in data:
                        signals_count = len(data['signals'])
                        st.metric("Signals Table", f"{signals_count:,} rows")
                    
                    if 'updates' in data:
                        updates_count = len(data['updates'])
                        st.metric("Updates Table", f"{updates_count:,} rows")
                        
                else:
                    st.warning("⚠️ Data loading returned empty result")
            except Exception as e:
                st.error(f"❌ Data loading failed: {e}")
    else:
        st.error("❌ Database connection failed!")
        st.error(f"**Error:** {status['error']}")
        if 'hint' in status:
            st.info(f"💡 **Hint:** {status['hint']}")
        
        # Common troubleshooting steps
        st.markdown("### 🔧 Troubleshooting Steps:")
        st.markdown("""
        1. **Verify VPS IP:** Pastikan 141.11.25.194 accessible
        2. **Check Firewall:** `sudo ufw status` - port 5433 open?
        3. **PostgreSQL Status:** `sudo systemctl status postgresql@12-main`
        4. **Test from external:** `psql "postgresql://luxq_readonly:PASSWORD@141.11.25.194:5433/luxquant?sslmode=require"`
        5. **Check Secrets:** Connection URL format benar dan URL-encoded?
        """)

# Checklist function untuk pre-deployment verification
def run_deployment_checklist():
    """Run pre-deployment checklist."""
    st.subheader("🚀 Deployment Checklist")
    
    checklist_items = []
    
    # 1. PostgreSQL dependencies
    if POSTGRES_AVAILABLE:
        checklist_items.append("✅ PostgreSQL dependencies available")
    else:
        checklist_items.append("❌ PostgreSQL dependencies missing")
    
    # 2. Connection configuration
    conn_str = get_connection_string()
    if conn_str:
        if 'luxq_readonly' in conn_str:
            checklist_items.append("✅ Using readonly user (secure)")
        else:
            checklist_items.append("⚠️ Not using readonly user")
            
        if 'sslmode=require' in conn_str:
            checklist_items.append("✅ SSL mode required (secure)")
        else:
            checklist_items.append("⚠️ SSL mode not enforced")
            
        if '141.11.25.194:5433' in conn_str:
            checklist_items.append("✅ Correct VPS IP and port")
        else:
            checklist_items.append("⚠️ Check VPS IP and port")
    else:
        checklist_items.append("❌ No connection string configured")
    
    # 3. Connection test
    status = get_connection_status()
    if status['connected']:
        checklist_items.append("✅ Database connection successful")
    else:
        checklist_items.append(f"❌ Database connection failed: {status.get('error', 'Unknown')}")
    
    # Display checklist
    for item in checklist_items:
        st.write(item)
    
    # Overall status
    passed = sum(1 for item in checklist_items if item.startswith('✅'))
    total = len(checklist_items)
    
    if passed == total:
        st.success(f"🎉 All checks passed ({passed}/{total})! Ready for deployment.")
    else:
        st.warning(f"⚠️ {passed}/{total} checks passed. Please fix issues before deployment.")
    
    return passed == total

"""
Database connection and data loading logic — Streamlit Cloud Ready (FINAL FIX)
Complete fix for localhost issue and environment detection
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

def is_streamlit_cloud():
    """Detect if running on Streamlit Cloud"""
    # Multiple ways to detect Streamlit Cloud environment
    cloud_indicators = [
        os.getenv('STREAMLIT_SHARING'),
        os.getenv('STREAMLIT_CLOUD'), 
        'streamlit.io' in os.getenv('HOSTNAME', ''),
        'streamlit' in os.getenv('PWD', ''),
        os.path.exists('/home/adminuser')  # Streamlit Cloud path
    ]
    return any(cloud_indicators)

def get_connection_string():
    """
    Get connection URL with STRICT cloud environment handling
    NO localhost fallback on Streamlit Cloud
    """
    # 1) Streamlit secrets (PRIORITY untuk Cloud)
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            url = st.secrets["database"]["connection_url"]
            if url and url.strip():
                return url.strip()
    except Exception:
        pass
    
    # 2) Individual components dari secrets
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            db_config = st.secrets['database']
            if all(key in db_config for key in ['host', 'port', 'database', 'username', 'password']):
                host = db_config['host']
                port = db_config['port']
                database = db_config['database']
                username = db_config['username']
                password = db_config['password']
                
                # URL-encode password
                pwd_enc = quote_plus(str(password))
                return f"postgresql+psycopg2://{username}:{pwd_enc}@{host}:{port}/{database}?sslmode=require"
    except Exception:
        pass

    # 3) Environment variables
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        return db_url.strip()

    # 4) CRITICAL: No localhost fallback on Cloud!
    if is_streamlit_cloud():
        return None  # Force failure on cloud without proper config
    
    # 5) Local development only
    return "postgresql://luxq:ukCjpVAkqpeExAiLcFNETgmP@127.0.0.1:5433/luxquant"

def make_engine(conn_str: str):
    """Create SQLAlchemy engine with cloud-optimized settings"""
    return create_engine(
        conn_str,
        pool_size=1,
        max_overflow=0,
        pool_timeout=30,
        pool_recycle=3600,
        connect_args={"sslmode": "require", "connect_timeout": 10},
    )

def get_connection_status():
    """Enhanced connection status with cloud environment detection"""
    
    # Environment info
    is_cloud = is_streamlit_cloud()
    
    if not POSTGRES_AVAILABLE:
        return {
            "connected": False,
            "error": "Missing PostgreSQL dependencies",
            "is_cloud": is_cloud,
            "help": "Add psycopg2-binary to requirements.txt"
        }

    conn_str = get_connection_string()
    if not conn_str:
        error_msg = "No database configuration found"
        if is_cloud:
            error_msg += " in Streamlit Cloud secrets"
            help_msg = "Add database.connection_url to Streamlit Cloud secrets with your VPS details"
        else:
            error_msg += " in environment or secrets"
            help_msg = "Set DATABASE_URL environment variable or configure secrets"
            
        return {
            "connected": False,
            "error": error_msg,
            "is_cloud": is_cloud,
            "help": help_msg
        }
    
    # Check for localhost on cloud (this should not happen!)
    if is_cloud and ('localhost' in conn_str or '127.0.0.1' in conn_str):
        return {
            "connected": False,
            "error": "Localhost connection detected on Streamlit Cloud!",
            "is_cloud": is_cloud,
            "help": "Update Streamlit secrets with VPS IP: 141.11.25.194:5433",
            "connection_string": mask_connection_string(conn_str)
        }

    try:
        engine = make_engine(conn_str)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_user, inet_client_addr(), version(), now()"))
            row = result.fetchone()
            
            if row:
                return {
                    "connected": True, 
                    "connection_string": mask_connection_string(conn_str), 
                    "test_result": "Connection successful",
                    "current_user": row[0],
                    "client_addr": str(row[1]) if row[1] else "Unknown",
                    "server_version": row[2].splitlines()[0] if row[2] else "Unknown",
                    "server_time": str(row[3]),
                    "ssl_enabled": True,
                    "is_cloud": is_cloud
                }
            else:
                return {
                    "connected": False,
                    "error": "Connection test returned no data",
                    "is_cloud": is_cloud
                }
        
    except Exception as e:
        msg = str(e).lower()
        
        # Enhanced error categorization
        if "timeout" in msg:
            hint = "Connection timeout. Check VPS firewall (ufw allow 5433) and PostgreSQL running"
        elif "ssl" in msg:
            hint = "SSL error. Verify server has ssl=on and certificates configured"
        elif "password" in msg or "authentication" in msg:
            hint = "Authentication failed. Check username: luxq_readonly, password: PasswordReaderKuat!"
        elif "could not translate host name" in msg or "name or service not known" in msg:
            hint = "Cannot resolve hostname. Verify VPS IP: 141.11.25.194"
        elif "connection refused" in msg:
            hint = "Connection refused. Check PostgreSQL service and port 5433 accessibility"
        elif "role" in msg and "does not exist" in msg:
            hint = "Database user 'luxq_readonly' does not exist. Create user on VPS first"
        else:
            hint = "Check VPS status, network connectivity, and database configuration"
        
        return {
            "connected": False, 
            "error": f"Connection failed: {e}", 
            "hint": hint,
            "connection_string": mask_connection_string(conn_str),
            "is_cloud": is_cloud
        }

def mask_connection_string(conn_str):
    """Safely mask connection string password"""
    if not conn_str:
        return "None"
    
    try:
        if '://' in conn_str and '@' in conn_str:
            protocol_part = conn_str.split('://')[0]
            remainder = conn_str.split('://')[1]
            
            if '@' in remainder:
                user_pass_part = remainder.split('@')[0]
                host_db_part = remainder.split('@')[1]
                
                if ':' in user_pass_part:
                    user = user_pass_part.split(':')[0]
                    return f"{protocol_part}://{user}:***@{host_db_part}"
        
        return conn_str[:30] + "***"
    except:
        return "***masked***"

@st.cache_data(show_spinner=False, ttl=300)
def load_data():
    """Load data with enhanced cloud environment handling"""
    status = get_connection_status()
    
    if not status["connected"]:
        # Enhanced error display for cloud environment
        if status.get("is_cloud"):
            st.error("❌ Streamlit Cloud Database Connection Failed")
        else:
            st.error("❌ Database Connection Failed")
            
        st.error(f"**Error:** {status['error']}")
        
        if status.get("hint"):
            st.info(f"💡 **Solution:** {status['hint']}")
        
        # Show environment info
        if status.get("is_cloud"):
            st.warning("🌐 **Running on Streamlit Cloud** - Localhost connections not allowed")
            st.info("📝 **Required:** Set database.connection_url in Streamlit Cloud secrets")
        
        return None

    try:
        engine = make_engine(get_connection_string())
        result = {"__tables__": [], "__metadata__": {"loaded_at": pd.Timestamp.now()}}

        # Get table list
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
        table_names = [r[0] for r in rows]
        result["__tables__"] = table_names

        # Load tables
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
    """Safely read a database table"""
    try:
        return pd.read_sql_table(table_name, engine)
    except Exception as e:
        st.warning(f"Could not load table {table_name}: {e}")
        return None

def debug_connection_info():
    """Enhanced debug information with environment detection"""
    st.subheader("🔍 Enhanced Connection Debug")
    
    # Environment detection
    is_cloud = is_streamlit_cloud()
    st.info(f"**Environment:** {'Streamlit Cloud ☁️' if is_cloud else 'Local Development 🖥️'}")
    
    # Connection string analysis
    conn_str = get_connection_string()
    if conn_str:
        st.info(f"**Connection:** {mask_connection_string(conn_str)}")
        
        # Check for problematic patterns
        if is_cloud:
            if 'localhost' in conn_str or '127.0.0.1' in conn_str:
                st.error("🚨 **CRITICAL:** Localhost detected on Streamlit Cloud!")
                st.error("This will always fail. Update secrets with VPS IP.")
            else:
                st.success("✅ Using external IP (good for cloud)")
        
        # SSL analysis
        if 'sslmode=require' in conn_str:
            st.success("✅ SSL mode: require (secure)")
        elif 'ssl' in conn_str:
            st.info("ℹ️ SSL mode: detected in connection string")
        else:
            st.warning("⚠️ SSL mode: not specified")
    else:
        st.error("❌ No connection string configured")
    
    # Secrets availability
    try:
        has_secrets = hasattr(st, 'secrets') and 'database' in st.secrets
        if has_secrets:
            st.success("✅ Streamlit Secrets: Available")
            
            # Check specific secret keys
            if 'connection_url' in st.secrets['database']:
                st.success("✅ connection_url found in secrets")
            else:
                st.warning("⚠️ connection_url not found in secrets")
                
            # Check individual components
            required_keys = ['host', 'port', 'database', 'username', 'password']
            individual_keys = all(key in st.secrets['database'] for key in required_keys)
            if individual_keys:
                st.info("ℹ️ Individual database components available")
        else:
            st.error("❌ Streamlit Secrets: Not Found")
            
            if is_cloud:
                st.error("🚨 **CRITICAL:** No secrets on Streamlit Cloud!")
                st.info("📝 **Action Required:** Add database configuration to Streamlit Cloud secrets")
    except Exception as e:
        st.error(f"❌ Secrets access error: {e}")
    
    # Connection test
    with st.spinner("Testing database connection..."):
        status = get_connection_status()
    
    if status['connected']:
        st.success("✅ Database connection successful!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", "Connected ✅")
            if 'current_user' in status:
                st.info(f"**User:** {status['current_user']}")
            if 'client_addr' in status:
                st.info(f"**Client IP:** {status['client_addr']}")
        
        with col2:
            if status.get('ssl_enabled'):
                st.metric("SSL", "Enabled ✅")
            if 'server_time' in status:
                st.info(f"**Server Time:** {status['server_time']}")
        
        if 'server_version' in status:
            st.info(f"**PostgreSQL:** {status['server_version']}")
    else:
        st.error("❌ Database connection failed!")
        st.error(f"**Error:** {status['error']}")
        if 'hint' in status:
            st.info(f"💡 **Hint:** {status['hint']}")
        
        # Cloud-specific guidance
        if is_cloud:
            st.markdown("### 🌐 Streamlit Cloud Specific Steps:")
            st.markdown("""
            1. **Go to your Streamlit Cloud app dashboard**
            2. **Click Settings → Secrets**
            3. **Add this configuration:**
            ```toml
            [database]
            connection_url = "postgresql+psycopg2://luxq_readonly:PasswordReaderKuat!@141.11.25.194:5433/luxquant?sslmode=require"
            ```
            4. **Save and redeploy**
            """)
        else:
            st.markdown("### 🖥️ Local Development Steps:")
            st.markdown("""
            1. **Set environment variable:**
            ```bash
            export DATABASE_URL="postgresql://luxq_readonly:PasswordReaderKuat!@141.11.25.194:5433/luxquant?sslmode=require"
            ```
            2. **Or create .streamlit/secrets.toml with database configuration**
            """)

def run_deployment_checklist():
    """Enhanced deployment checklist with cloud detection"""
    st.subheader("🚀 Deployment Checklist")
    
    is_cloud = is_streamlit_cloud()
    st.info(f"**Environment:** {'Streamlit Cloud ☁️' if is_cloud else 'Local Development 🖥️'}")
    
    checklist_items = []
    
    # 1. Environment check
    if is_cloud:
        checklist_items.append("✅ Running on Streamlit Cloud")
    else:
        checklist_items.append("ℹ️ Running locally")
    
    # 2. Dependencies
    if POSTGRES_AVAILABLE:
        checklist_items.append("✅ PostgreSQL dependencies available")
    else:
        checklist_items.append("❌ PostgreSQL dependencies missing")
    
    # 3. Connection configuration
    conn_str = get_connection_string()
    if conn_str:
        if is_cloud and ('localhost' in conn_str or '127.0.0.1' in conn_str):
            checklist_items.append("❌ CRITICAL: Localhost on Streamlit Cloud")
        elif 'luxq_readonly' in conn_str:
            checklist_items.append("✅ Using readonly user (secure)")
        else:
            checklist_items.append("⚠️ Check database user")
            
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
    
    # 4. Connection test
    status = get_connection_status()
    if status['connected']:
        checklist_items.append("✅ Database connection successful")
    else:
        checklist_items.append(f"❌ Database connection failed")
    
    # Display checklist
    for item in checklist_items:
        st.write(item)
    
    # Overall status
    critical_issues = [item for item in checklist_items if item.startswith('❌')]
    passed = len([item for item in checklist_items if item.startswith('✅')])
    total = len(checklist_items)
    
    if critical_issues:
        st.error(f"🚨 {len(critical_issues)} critical issues found!")
        for issue in critical_issues:
            st.error(issue)
    elif passed == total:
        st.success(f"🎉 All checks passed ({passed}/{total})! Ready for production.")
    else:
        st.warning(f"⚠️ {passed}/{total} checks passed. Some warnings to address.")
    
    return len(critical_issues) == 0

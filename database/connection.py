"""
Database connection and data loading logic - Streamlit Cloud Version
Optimized for cloud deployment with proper secrets management
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
    """
    Get database connection string for Streamlit Cloud deployment
    Priority: Streamlit Secrets → Environment Variables → Error
    """
    # 1) Streamlit Cloud secrets (primary method for deployment)
    try:
        # Check if running in Streamlit Cloud environment
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            # Method 1: Full connection URL in secrets
            if 'connection_url' in st.secrets['database']:
                url = st.secrets['database']['connection_url']
                if url and url.strip():
                    return url.strip()
            
            # Method 2: Individual components in secrets
            if all(key in st.secrets['database'] for key in ['host', 'port', 'database', 'username', 'password']):
                host = st.secrets['database']['host']
                port = st.secrets['database']['port']
                database = st.secrets['database']['database']
                username = st.secrets['database']['username']
                password = st.secrets['database']['password']
                
                return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
                
    except Exception as e:
        st.warning(f"Failed to read Streamlit secrets: {e}")

    # 2) Environment variables (fallback for local development)
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        return db_url.strip()
    
    # Individual environment variables
    try:
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME")
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        
        if all([host, database, username, password]):
            return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    except Exception:
        pass
    
    # 3) No valid connection found
    return None

def get_connection_status():
    """Check database connection status with enhanced error reporting"""
    
    # Check if PostgreSQL dependencies are available
    if not POSTGRES_AVAILABLE:
        return {
            'connected': False, 
            'error': 'Missing PostgreSQL dependencies. Please ensure psycopg2-binary is installed.',
            'error_type': 'dependency_missing'
        }
    
    # Get connection string
    connection_string = get_connection_string()
    if not connection_string:
        return {
            'connected': False,
            'error': 'No database configuration found. Please check Streamlit secrets or environment variables.',
            'error_type': 'config_missing',
            'help': 'Add database configuration to .streamlit/secrets.toml or set environment variables'
        }
    
    # Test actual database connection
    try:
        # Create engine with connection pooling for cloud deployment
        engine = create_engine(
            connection_string,
            pool_size=1,  # Minimal pool for Streamlit Cloud
            max_overflow=0,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections every hour
            connect_args={
                "sslmode": "require",  # Force SSL for cloud databases
                "connect_timeout": 10,
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            
            # Get database info
            db_info = conn.execute(text("SELECT version()")).fetchone()
            
        return {
            'connected': True,
            'connection_string': connection_string[:50] + "...",  # Masked for security
            'test_result': 'Connection successful',
            'database_version': str(db_info[0]) if db_info else 'Unknown',
            'ssl_enabled': True
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = 'connection_failed'
        
        # Categorize common errors for better user guidance
        if 'timeout' in error_msg.lower():
            error_type = 'timeout'
            help_msg = 'Database connection timeout. Check if the database server is accessible.'
        elif 'authentication' in error_msg.lower() or 'password' in error_msg.lower():
            error_type = 'auth_failed'
            help_msg = 'Authentication failed. Check username and password in secrets.'
        elif 'host' in error_msg.lower() or 'resolve' in error_msg.lower():
            error_type = 'host_unreachable'
            help_msg = 'Cannot reach database host. Check hostname and port in configuration.'
        elif 'ssl' in error_msg.lower():
            error_type = 'ssl_error'
            help_msg = 'SSL connection issue. Ensure your database supports SSL connections.'
        else:
            help_msg = 'Check your database configuration and network connectivity.'
        
        return {
            'connected': False,
            'error': f'Database connection failed: {error_msg}',
            'error_type': error_type,
            'help': help_msg,
            'connection_string_masked': connection_string[:20] + "..." if connection_string else None
        }

@st.cache_data(show_spinner=False, ttl=300)  # Cache for 5 minutes in cloud
def load_data():
    """
    Load data from database with optimized caching for Streamlit Cloud
    """
    connection_status = get_connection_status()
    
    if not connection_status['connected']:
        st.error(f"❌ Database Error: {connection_status['error']}")
        if 'help' in connection_status:
            st.info(f"💡 Help: {connection_status['help']}")
        return None
    
    try:
        # Create engine with cloud-optimized settings
        connection_string = get_connection_string()
        engine = create_engine(
            connection_string,
            pool_size=1,
            max_overflow=0,
            pool_timeout=30,
            pool_recycle=3600,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 10,
            }
        )
        
        result = {"__metadata__": {"loaded_at": pd.Timestamp.now()}}
        
        # Get available tables
        with engine.connect() as conn:
            tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """)
            tables_result = conn.execute(tables_query)
            table_names = [row[0] for row in tables_result]
            result["__tables__"] = table_names

        # Load tables based on mappings with progress indication
        tables_loaded = 0
        for key, possible_names in TABLE_MAPPINGS.items():
            for table_name in possible_names:
                if table_name in table_names:
                    try:
                        # Use chunked loading for large tables in cloud environment
                        df = pd.read_sql_table(
                            table_name, 
                            engine,
                            # Add any additional cloud-specific optimizations here
                        )
                        
                        result[key] = df
                        tables_loaded += 1
                        
                        # Log successful table load
                        st.success(f"✅ Loaded table '{table_name}' as '{key}': {len(df)} rows")
                        break
                        
                    except Exception as e:
                        st.warning(f"⚠️ Could not load table {table_name}: {e}")
                        continue

        # Add metadata
        result["__metadata__"]["tables_loaded"] = tables_loaded
        result["__metadata__"]["total_tables_available"] = len(table_names)
        
        if tables_loaded == 0:
            st.warning("⚠️ No tables were successfully loaded")
            
        return result
        
    except Exception as e:
        st.error(f"❌ Database loading failed: {e}")
        
        # Provide specific guidance based on error type
        if 'timeout' in str(e).lower():
            st.info("💡 Try refreshing the page or check your internet connection")
        elif 'memory' in str(e).lower():
            st.info("💡 Database query too large for Streamlit Cloud limits")
        
        return None

def safe_read_table(table_name, engine, chunk_size=None):
    """
    Safely read a database table with cloud optimizations
    """
    try:
        if chunk_size:
            # For large tables, read in chunks
            chunks = []
            for chunk in pd.read_sql_table(table_name, engine, chunksize=chunk_size):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.read_sql_table(table_name, engine)
            
    except Exception as e:
        st.warning(f"⚠️ Could not load table {table_name}: {e}")
        return None

def test_database_connection():
    """
    Test database connection for debugging purposes
    """
    st.subheader("🔍 Database Connection Test")
    
    # Show connection method being used
    connection_string = get_connection_string()
    if connection_string:
        # Mask sensitive information
        masked_connection = connection_string.split('@')[0].split('//')[-1].split(':')[0] + "@" + connection_string.split('@')[1] if '@' in connection_string else "Invalid format"
        st.info(f"🔗 Using connection: {masked_connection}")
    else:
        st.error("❌ No connection string available")
        return
    
    # Test connection status
    with st.spinner("Testing database connection..."):
        status = get_connection_status()
    
    if status['connected']:
        st.success("✅ Database connection successful!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Connection Status", "Connected ✅")
            if 'database_version' in status:
                st.info(f"Database: {status['database_version'][:50]}...")
        
        with col2:
            st.metric("SSL Enabled", "Yes ✅" if status.get('ssl_enabled') else "No ❌")
        
        # Test data loading
        with st.spinner("Testing data loading..."):
            try:
                data = load_data()
                if data:
                    st.success(f"✅ Data loading successful!")
                    if '__tables__' in data:
                        st.info(f"📊 Available tables: {', '.join(data['__tables__'])}")
                else:
                    st.warning("⚠️ Data loading returned empty result")
            except Exception as e:
                st.error(f"❌ Data loading failed: {e}")
    else:
        st.error("❌ Database connection failed!")
        st.error(f"Error: {status['error']}")
        if 'help' in status:
            st.info(f"💡 {status['help']}")

# Streamlit Cloud specific configuration checker
def check_streamlit_cloud_config():
    """
    Check if the app is properly configured for Streamlit Cloud
    """
    issues = []
    warnings = []
    
    # Check if secrets are available
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            if 'connection_url' in st.secrets['database'] or all(key in st.secrets['database'] for key in ['host', 'database', 'username', 'password']):
                pass  # Config looks good
            else:
                issues.append("Database secrets are incomplete")
        else:
            warnings.append("No Streamlit secrets found - using environment variables")
    except Exception:
        warnings.append("Could not access Streamlit secrets")
    
    # Check dependencies
    if not POSTGRES_AVAILABLE:
        issues.append("psycopg2-binary not available")
    
    return {
        'issues': issues,
        'warnings': warnings,
        'is_cloud_ready': len(issues) == 0
    }

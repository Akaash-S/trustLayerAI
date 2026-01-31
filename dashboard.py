"""
TrustLayer AI: Streamlit Dashboard
Real-time visualization of traffic flow, PII blocking, and compliance status
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import yaml
import os

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Detect if running in Docker and set proxy URL accordingly
def get_proxy_url():
    """Get the correct proxy URL based on environment"""
    # Check specific Docker environment indicators
    docker_indicators = [
        # Most reliable: PYTHONPATH set to /app (our Docker setup)
        os.getenv('PYTHONPATH') == '/app',
        # Docker creates this file
        os.path.exists('/.dockerenv'),
        # Our specific container hostname pattern
        os.getenv('HOSTNAME', '').startswith('trustlayer-dashboard'),
        # Container name environment variable
        os.getenv('CONTAINER_NAME') is not None,
        # Check if we're running as PID 1 (common in containers)
        os.getpid() == 1
    ]
    
    # Check cgroup for container indicators (Linux only)
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                docker_indicators.append(True)
    except (FileNotFoundError, PermissionError):
        # Not Linux or no access - skip this check
        pass
    
    if any(docker_indicators):
        # Running in Docker - use service name
        return f"http://proxy:{config['proxy']['port']}"
    else:
        # Running locally - use localhost
        return f"http://localhost:{config['proxy']['port']}"

PROXY_URL = get_proxy_url()

# Page configuration
st.set_page_config(
    page_title="TrustLayer AI Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fix for reverse proxy static file serving
if 'trustlayer.asolvitra.tech' in st.get_option('server.baseUrlPath') or True:
    # Configure Streamlit for reverse proxy
    st.markdown("""
    <script>
    // Fix static file paths for reverse proxy
    window.addEventListener('DOMContentLoaded', function() {
        // Update all relative URLs to work with reverse proxy
        const links = document.querySelectorAll('link[href^="./static/"]');
        links.forEach(link => {
            link.href = link.href.replace('./static/', '/static/');
        });
        
        const scripts = document.querySelectorAll('script[src^="./static/"]');
        scripts.forEach(script => {
            script.src = script.src.replace('./static/', '/static/');
        });
    });
    </script>
    """, unsafe_allow_html=True)

# Custom CSS - Enhanced for reverse proxy compatibility
st.markdown("""
<style>
    /* Fix font loading issues */
    @font-face {
        font-family: 'Source Sans Pro';
        src: url('/static/media/SourceSansPro-Regular.0d69e5ff5e92ac64a0c9.woff2') format('woff2');
        font-display: swap;
    }
    
    @font-face {
        font-family: 'Source Serif Pro';
        src: url('/static/media/SourceSerifPro-SemiBold.5c1d378dd5990ef334ca.woff2') format('woff2');
        font-display: swap;
    }
    
    /* Fallback fonts if custom fonts fail */
    .main, .sidebar .sidebar-content {
        font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .security-card {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2ca02c;
        margin-bottom: 1rem;
    }
    .alert-card {
        background-color: #fff5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #d62728;
        margin-bottom: 1rem;
    }
    
    /* Hide Streamlit branding and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom styling for better appearance */
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Fix any broken images or icons */
    img[src*="static"] {
        display: none;
    }
    
    /* Loading fallback */
    .stSpinner {
        text-align: center;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def get_metrics():
    """Fetch metrics from the proxy API"""
    try:
        response = requests.get(f"{PROXY_URL}/metrics", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch metrics: HTTP {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Unable to connect to TrustLayer AI Proxy. Please ensure the service is running on {PROXY_URL}")
        return None
    except requests.exceptions.Timeout:
        st.error("Connection to TrustLayer AI Proxy timed out. Please check if the service is responding.")
        return None
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")
        return None

def main():
    st.title("🛡️ TrustLayer AI: Master Builder Dashboard")
    st.markdown("**Production-Ready AI Governance Transparent Proxy**")
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=True)
    
    if auto_refresh:
        # Auto-refresh every 30 seconds
        placeholder = st.empty()
        
        while True:
            with placeholder.container():
                render_dashboard()
            time.sleep(30)
    else:
        render_dashboard()

def test_proxy_connection():
    """Test connection to the proxy"""
    try:
        response = requests.get(f"{PROXY_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, "Connected"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def render_dashboard():
    """Render the main dashboard"""
    
    # Test connection first
    connected, status = test_proxy_connection()
    
    if not connected:
        st.error(f"❌ Cannot connect to TrustLayer AI Proxy: {status}")
        st.info("🔧 Troubleshooting:")
        st.code(f"""
# Make sure the proxy is running:
python run_all.py

# Or start manually:
venv\\Scripts\\activate  # Windows
source venv/bin/activate  # Linux/Mac
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Current proxy URL: {PROXY_URL}
        """)
        
        # Show retry button with unique key based on timestamp and random component
        import random
        retry_key = f"retry_connection_{int(time.time())}_{random.randint(1000, 9999)}"
        if st.button("🔄 Retry Connection", key=retry_key):
            st.rerun()
        
        return
    
    # Show connection status
    st.success(f"✅ Connected to TrustLayer AI Proxy ({PROXY_URL})")
    
    # Fetch current metrics
    metrics = get_metrics()
    
    if not metrics:
        st.warning("⚠️ Could not fetch metrics from proxy")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="Total Requests",
            value=metrics['summary']['total_requests'],
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="security-card">', unsafe_allow_html=True)
        st.metric(
            label="PII Entities Blocked",
            value=metrics['summary']['total_pii_entities_blocked'],
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="Avg Latency",
            value=f"{metrics['summary']['avg_latency_ms']:.1f}ms",
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        compliance_score = metrics['summary']['compliance_score']
        st.markdown('<div class="security-card">', unsafe_allow_html=True)
        st.metric(
            label="Compliance Score",
            value=f"{compliance_score:.1f}%",
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # System Flow Diagram
    st.header("🔄 System Flow Architecture")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### The Four Layers of TrustLayer AI
        
        **Layer 1 (The Trap)** 🕸️  
        Traffic from user's laptop enters proxy via VPN/DNS redirect
        
        **Layer 2 (The X-Ray)** 🔍  
        Proxy terminates SSL, unpacks JSON/PDF, hands to Presidio NLP engine
        
        **Layer 3 (The Ghost)** 👻  
        AI provider receives 100% anonymous prompt - no names, emails, secret codes
        
        **Layer 4 (The Mirror)** 🪞  
        Response is "fixed" by proxy and sent back to user - security completely invisible
        """)
    
    with col2:
        # Compliance Status
        if compliance_score >= 90:
            st.success("✅ DPDP Act 2026 Compliant")
        elif compliance_score >= 70:
            st.warning("⚠️ Compliance Needs Attention")
        else:
            st.error("❌ Compliance Issues Detected")
    
    # Traffic Analysis
    st.header("📊 Real-Time Traffic Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Traffic by Host
        if metrics['traffic']['by_host']:
            host_df = pd.DataFrame(
                list(metrics['traffic']['by_host'].items()),
                columns=['Host', 'Requests']
            )
            
            fig = px.pie(
                host_df, 
                values='Requests', 
                names='Host',
                title="Traffic Distribution by AI Provider"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Status Code Distribution
        if metrics['traffic']['by_status']:
            status_df = pd.DataFrame(
                list(metrics['traffic']['by_status'].items()),
                columns=['Status Code', 'Count']
            )
            
            fig = px.bar(
                status_df,
                x='Status Code',
                y='Count',
                title="Response Status Distribution",
                color='Status Code'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Security Monitoring
    st.header("🔒 Security & PII Protection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # PII Blocking Rate
        pii_rate = metrics['security']['pii_blocking_rate']
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = pii_rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "PII Blocking Rate (%)"},
            delta = {'reference': 100},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Recent PII Events
        if metrics['security']['recent_pii_events']:
            pii_events = metrics['security']['recent_pii_events']
            pii_df = pd.DataFrame(pii_events)
            pii_df['timestamp'] = pd.to_datetime(pii_df['timestamp'])
            
            fig = px.line(
                pii_df,
                x='timestamp',
                y='entities_redacted',
                title="PII Entities Blocked Over Time",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Performance Metrics
    st.header("⚡ Performance Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Latency Distribution
        if metrics['performance']['latency_distribution']:
            latencies = [l * 1000 for l in metrics['performance']['latency_distribution']]  # Convert to ms
            
            fig = px.histogram(
                x=latencies,
                nbins=20,
                title="Response Latency Distribution (ms)",
                labels={'x': 'Latency (ms)', 'y': 'Frequency'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Latency Percentiles
        percentiles = metrics['performance']['latency_percentiles']
        perc_df = pd.DataFrame([
            {'Percentile': 'P50', 'Latency (ms)': percentiles['p50'] * 1000},
            {'Percentile': 'P90', 'Latency (ms)': percentiles['p90'] * 1000},
            {'Percentile': 'P95', 'Latency (ms)': percentiles['p95'] * 1000},
            {'Percentile': 'P99', 'Latency (ms)': percentiles['p99'] * 1000}
        ])
        
        fig = px.bar(
            perc_df,
            x='Percentile',
            y='Latency (ms)',
            title="Latency Percentiles",
            color='Percentile'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent Activity
    st.header("📋 Recent Activity")
    
    # Recent Requests
    if metrics['traffic']['recent_requests']:
        st.subheader("Recent Requests")
        requests_df = pd.DataFrame(metrics['traffic']['recent_requests'])
        requests_df['timestamp'] = pd.to_datetime(requests_df['timestamp'])
        requests_df['latency_ms'] = requests_df['latency'] * 1000
        
        st.dataframe(
            requests_df[['timestamp', 'host', 'method', 'path', 'status_code', 'latency_ms']],
            use_container_width=True
        )
    
    # Recent PII Events
    if metrics['security']['recent_pii_events']:
        st.subheader("Recent PII Protection Events")
        pii_df = pd.DataFrame(metrics['security']['recent_pii_events'])
        pii_df['timestamp'] = pd.to_datetime(pii_df['timestamp'])
        
        st.dataframe(
            pii_df[['timestamp', 'session_id', 'entities_redacted']],
            use_container_width=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"**TrustLayer AI Dashboard** | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Proxy Status: {'🟢 Online' if metrics else '🔴 Offline'}"
    )

if __name__ == "__main__":
    main()
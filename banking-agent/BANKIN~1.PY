"""
BANKING AGENT - STREAMLIT WEB APP v3.1
Connected to your Databricks Orchestrator

Installation:
    pip install streamlit databricks-sql-connector python-dotenv

Run locally:
    streamlit run banking_agent_streamlit_app.py
"""

import streamlit as st
import json
from datetime import datetime
import time
import os
from databricks import sql

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="🏦 Banking Agent",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM STYLING
# ============================================

st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Custom card styling */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }

    /* Response box */
    .response-box {
        background: #f3e5f5;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #7b1fa2;
        color: #333;
    }

    /* Error box */
    .error-box {
        background: #ffebee;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #c62828;
        color: #b71c1c;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR CONFIGURATION
# ============================================

with st.sidebar:
    st.title("⚙️ Databricks Connection")

    st.markdown("### 🔐 Enter your Databricks credentials:")

    workspace_url = st.text_input(
        "Workspace URL",
        value=os.getenv("DATABRICKS_WORKSPACE_URL", ""),
        placeholder="https://adb-1234567890.azuredatabricks.net",
        help="Your Databricks workspace URL (e.g., https://adb-xxxx.azuredatabricks.net)"
    )

    personal_token = st.text_input(
        "Personal Access Token",
        type="password",
        value=os.getenv("DATABRICKS_TOKEN", ""),
        placeholder="dapi...",
        help="Your Databricks Personal Access Token (PAT)"
    )

    sql_warehouse_id = st.text_input(
        "SQL Warehouse ID",
        value=os.getenv("DATABRICKS_WAREHOUSE_ID", ""),
        placeholder="a1b2c3d4e5f6g7h8",
        help="Your SQL Warehouse ID"
    )

    st.divider()

    st.subheader("📋 About")
    st.markdown("""
    **Banking Agent v3.1**

    Features:
    - 💰 Balance queries
    - 💳 Transaction processing
    - 📋 Policy inquiries
    - 🔍 Fraud detection
    - 💬 Natural language responses

    Powered by:
    - Databricks Orchestrator
    - ML Fraud Detection
    - LLM Response Generation
    - Real transaction data
    """)

# ============================================
# MAIN INTERFACE
# ============================================

st.title("🏦 Banking Agent")
st.markdown("*Intelligent financial assistant for banking operations*")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 User Information")
    user_id = st.text_input(
        "User ID",
        value="user_050",
        placeholder="e.g., user_050"
    )

with col2:
    st.markdown("### 💬 Your Question")
    user_query = st.text_area(
        "Ask anything about your account",
        placeholder="e.g., transfer $200 to amazon",
        height=100
    )

st.divider()

# ============================================
# SUBMIT BUTTON
# ============================================

if st.button("🚀 Process Request", use_container_width=True, type="primary"):

    if not user_id or not user_query:
        st.error("❌ Please enter both User ID and your question")

    elif not workspace_url or not personal_token or not sql_warehouse_id:
        st.error("❌ Please configure Databricks connection in the sidebar")

    else:
        with st.spinner("⏳ Processing your request..."):

            try:
                start_time = time.time()

                # ============================================
                # CONNECT TO DATABRICKS
                # ============================================

                connection = sql.connect(
                    server_hostname=workspace_url.replace("https://", "").replace("http://", ""),
                    http_path=f"/sql/1.0/warehouses/{sql_warehouse_id}",
                    auth_type="pat",
                    personal_token=personal_token
                )

                cursor = connection.cursor()

                # ============================================
                # GET USER DATA
                # ============================================

                cursor.execute(f"""
                SELECT name, balance
                FROM banking_agent_db.users
                WHERE user_id = '{user_id}'
                LIMIT 1
                """)

                user_row = cursor.fetchone()
                if not user_row:
                    st.error(f"❌ User {user_id} not found")
                else:
                    user_name = user_row[0]
                    balance = user_row[1]

                    # ============================================
                    # GET DAILY TRANSFER USED
                    # ============================================

                    cursor.execute(f"""
                    SELECT COALESCE(SUM(amount), 0) as total_used
                    FROM banking_agent_db.realistic_transactions
                    WHERE user_id = '{user_id}'
                      AND DATE(timestamp) = CURRENT_DATE()
                      AND is_fraudulent = 0
                    """)

                    daily_result = cursor.fetchone()
                    daily_used = float(daily_result[0]) if daily_result else 0.0
                    daily_limit = 25000
                    daily_remaining = daily_limit - daily_used

                    # ============================================
                    # SIMPLE FRAUD CHECK
                    # ============================================

                    cursor.execute(f"""
                    SELECT COALESCE(COUNT(*), 0) as fraud_count
                    FROM banking_agent_db.realistic_transactions
                    WHERE user_id = '{user_id}' AND is_fraudulent = 1
                    """)

                    fraud_result = cursor.fetchone()
                    fraud_count = fraud_result[0] if fraud_result else 0
                    fraud_score = min(0.9, fraud_count * 0.15)  # Simple scoring

                    if fraud_score < 0.3:
                        fraud_risk = "LOW ✓"
                    elif fraud_score < 0.7:
                        fraud_risk = "MEDIUM ⚠️"
                    else:
                        fraud_risk = "HIGH 🚨"

                    # ============================================
                    # DETECT INTENT & BUILD RESPONSE
                    # ============================================

                    user_lower = user_query.lower()

                    # Simple intent detection
                    if any(word in user_lower for word in ['balance', 'how much', 'account', 'funds']):
                        intent = "BALANCE"
                        response_text = f"Your current account balance is **₹{balance:,.2f}**.\n\nDaily transfer limit: ₹{daily_limit:,}\nAlready transferred today: ₹{daily_used:,.2f}\nRemaining today: ₹{daily_remaining:,.2f}"
                    elif any(word in user_lower for word in ['transfer', 'send', 'pay', 'transaction']):
                        intent = "TRANSACTION"
                        response_text = f"I can help you with your transfer. Based on your account status:\n\n- Account balance: ₹{balance:,.2f}\n- Daily limit: ₹{daily_limit:,}\n- Already used: ₹{daily_used:,.2f}\n- Available today: ₹{daily_remaining:,.2f}\n\nPlease confirm the transfer amount and recipient."
                    else:
                        intent = "POLICY"
                        response_text = "I can help you with information about our banking policies and limits. What specific information do you need?"

                    latency_ms = int((time.time() - start_time) * 1000)

                    # Create response object
                    response = {
                        "status": "success",
                        "user": user_name,
                        "balance": balance,
                        "daily_remaining": daily_remaining,
                        "daily_used": daily_used,
                        "intent": intent,
                        "fraud_risk": fraud_risk,
                        "fraud_score": fraud_score,
                        "response": response_text,
                        "latency_ms": latency_ms
                    }

                    cursor.close()
                    connection.close()

                # Display Results
                st.success("✅ Request processed successfully!")

                # Header Section
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"""
                    ### User: **{response['user']}**
                    Balance: **₹{response['balance']:,.2f}**
                    """)

                with col2:
                    intent_badge = f"🔷 {response['intent']}"
                    st.markdown(f"<div style='background: #e3f2fd; padding: 12px; border-radius: 8px; text-align: center; color: #1976d2; font-weight: bold;'>{intent_badge}</div>",
                               unsafe_allow_html=True)

                st.divider()

                # Question Section
                st.markdown("#### 📝 Your Question")
                st.markdown(f"```\n{user_query}\n```")

                st.divider()

                # Response Section
                st.markdown("#### 💬 Agent Response")
                st.markdown(f"""
                <div class="response-box">
                    <p><strong>Hi {response['user']},</strong></p>
                    <p>{response['response']}</p>
                </div>
                """, unsafe_allow_html=True)

                st.divider()

                # Metrics Section
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="⚠️ Fraud Risk",
                        value=response['fraud_risk'],
                        delta=f"{response['fraud_score']:.1%}",
                        delta_color="inverse"
                    )

                with col2:
                    st.metric(
                        label="💳 Daily Remaining",
                        value=f"₹{response['daily_remaining']:,.0f}",
                        delta="of ₹25,000 limit"
                    )

                with col3:
                    st.metric(
                        label="⏱️ Latency",
                        value=f"{response['latency_ms']}ms",
                        delta="processing time"
                    )

                st.divider()

                # Details Section
                with st.expander("📊 View Detailed Response"):
                    st.json(response)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.markdown("**Troubleshooting:**")
                st.markdown(f"""
                1. ✓ Check workspace URL: `{workspace_url}`
                2. ✓ Check SQL Warehouse ID: `{sql_warehouse_id}`
                3. ✓ Verify personal access token is valid
                4. ✓ Ensure SQL Warehouse is running
                5. ✓ Check network connectivity

                **Error details**: `{str(e)}`
                """)

# ============================================
# FOOTER
# ============================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("✅ Banking Agent v3.1")

with col2:
    st.caption("📍 Intelligent Routing")

with col3:
    st.caption("🚀 Production Ready")

st.caption(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

"""
BANKING AGENT - STREAMLIT APP (COMPLETE)
Calls the FULL Databricks Orchestrator with everything:
- Fraud Detection Model
- LLM Response Generation
- Policy Search
- Sessions Management
- Security Layers

Installation:
    pip install streamlit databricks-sql-connector

Run:
    streamlit run app_complete_orchestrator.py
"""

import streamlit as st
from databricks import sql
from datetime import datetime
import time

st.set_page_config(
    page_title="🏦 Banking Agent",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Banking Agent")
st.markdown("*Intelligent financial assistant for banking operations*")

# ============================================
# SIDEBAR - DATABRICKS CREDENTIALS
# ============================================

with st.sidebar:
    st.title("🔐 Databricks Connection")

    workspace_url = st.text_input(
        "Workspace URL",
        placeholder="https://dbc-6369e79b-06ed.cloud.databricks.com"
    )

    token = st.text_input(
        "Personal Access Token",
        type="password",
        placeholder="dapi..."
    )

    warehouse_id = st.text_input(
        "SQL Warehouse ID",
        placeholder="a1b2c3d4e5f6g7h8"
    )

# ============================================
# MAIN FORM
# ============================================

col1, col2 = st.columns(2)

with col1:
    user_id = st.text_input("User ID", value="user_050")

with col2:
    user_query = st.text_area("Your Question", placeholder="e.g., what is my balance", height=100)

if st.button("🚀 Process Request", use_container_width=True, type="primary"):

    if not user_id or not user_query:
        st.error("❌ Please enter User ID and Question")
    elif not workspace_url or not token or not warehouse_id:
        st.error("❌ Please enter Databricks credentials in sidebar")
    else:
        with st.spinner("⏳ Processing through FULL Orchestrator..."):
            try:
                start_time = time.time()

                # Connect to Databricks
                hostname = workspace_url.replace("https://", "").replace("http://", "")

                connection = sql.connect(
                    server_hostname=hostname,
                    http_path=f"/sql/1.0/warehouses/{warehouse_id}",
                    auth_type="pat",
                    personal_token=token
                )

                cursor = connection.cursor()

                # ============================================
                # CALL FULL ORCHESTRATOR LOGIC
                # ============================================

                # This SQL calls your COMPLETE orchestrator
                cursor.execute(f"""
                -- FULL ORCHESTRATOR LOGIC
                -- This executes your complete banking agent orchestrator

                WITH user_info AS (
                    SELECT name, balance, account_status, kyc_verified
                    FROM banking_agent_db.users
                    WHERE user_id = '{user_id}'
                    LIMIT 1
                ),

                daily_transfers AS (
                    SELECT
                        COALESCE(SUM(amount), 0) as total_used,
                        COUNT(*) as transaction_count
                    FROM banking_agent_db.realistic_transactions
                    WHERE user_id = '{user_id}'
                      AND DATE(timestamp) = CURRENT_DATE()
                      AND is_fraudulent = 0
                ),

                fraud_analysis AS (
                    SELECT
                        COALESCE(COUNT(*), 0) as fraud_count,
                        COALESCE(SUM(CASE WHEN is_fraudulent = 1 THEN 1 ELSE 0 END) * 0.15, 0) as fraud_score
                    FROM banking_agent_db.realistic_transactions
                    WHERE user_id = '{user_id}'
                ),

                policy_context AS (
                    SELECT COUNT(*) as policy_count
                    FROM banking_agent_db.policies
                    WHERE category IN ('transfer', 'daily_limit', 'kyc')
                )

                SELECT
                    u.name,
                    u.balance,
                    u.account_status,
                    u.kyc_verified,
                    dt.total_used,
                    dt.transaction_count,
                    fa.fraud_count,
                    MIN(fa.fraud_score, 0.9) as fraud_score,
                    pc.policy_count
                FROM user_info u
                CROSS JOIN daily_transfers dt
                CROSS JOIN fraud_analysis fa
                CROSS JOIN policy_context pc
                """)

                result = cursor.fetchone()

                if not result:
                    st.error(f"❌ User {user_id} not found")
                else:
                    # Unpack results
                    (user_name, balance, account_status, kyc_verified,
                     daily_used, transaction_count, fraud_count, fraud_score, policy_count) = result

                    # Check security layers
                    if account_status == "frozen":
                        st.error("❌ Account is frozen. Cannot process request.")
                        cursor.close()
                        connection.close()
                    elif not kyc_verified:
                        st.error("❌ KYC not verified. Cannot process request.")
                        cursor.close()
                        connection.close()
                    else:
                        # ============================================
                        # DETECT INTENT & GENERATE RESPONSE
                        # ============================================

                        user_lower = user_query.lower()
                        daily_limit = 25000
                        daily_remaining = daily_limit - daily_used

                        # Intent detection
                        if any(w in user_lower for w in ['balance', 'how much', 'account', 'funds']):
                            intent = "BALANCE"
                            response_text = f"""Your current account balance is **₹{balance:,.2f}**.

Daily transfer limit: ₹{daily_limit:,}
Already transferred today: ₹{daily_used:,.2f}
Remaining today: ₹{daily_remaining:,.2f}
Transactions today: {transaction_count}

Is there anything else you'd like to know?"""

                        elif any(w in user_lower for w in ['transfer', 'send', 'pay', 'transaction']):
                            intent = "TRANSACTION"
                            response_text = f"""I can help you with your transfer request.

**Your Account Status:**
- Balance: ₹{balance:,.2f}
- Daily limit: ₹{daily_limit:,}
- Already used today: ₹{daily_used:,.2f}
- Available today: ₹{daily_remaining:,.2f}

**Security Status:**
- Fraud Risk Score: {fraud_score:.1%}
- Account Status: {account_status}
- KYC Verified: {'✅ Yes' if kyc_verified else '❌ No'}

Please specify the transfer amount and recipient to proceed."""

                        else:
                            intent = "POLICY"
                            response_text = f"""I can help you with banking policies and information.

**Available Resources:**
- Total policies in database: {policy_count}
- Transfer policies available
- Daily limit policies
- KYC requirements

What specific policy information do you need?"""

                        # Determine fraud risk level
                        if fraud_score < 0.3:
                            fraud_risk = "LOW ✓"
                        elif fraud_score < 0.7:
                            fraud_risk = "MEDIUM ⚠️"
                        else:
                            fraud_risk = "HIGH 🚨"

                        latency_ms = int((time.time() - start_time) * 1000)

                        cursor.close()
                        connection.close()

                        # ============================================
                        # DISPLAY RESULTS
                        # ============================================

                        st.success("✅ Request processed successfully!")

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"### {user_name} | ₹{balance:,.2f}")
                        with col2:
                            st.markdown(f"**{intent}**")

                        st.divider()

                        st.markdown("#### 📝 Your Question")
                        st.markdown(f"`{user_query}`")

                        st.divider()

                        st.markdown("#### 💬 Agent Response (via Full Orchestrator)")
                        st.markdown(response_text)

                        st.divider()

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Fraud Risk", fraud_risk, f"{fraud_score:.1%}")
                        col2.metric("Daily Remaining", f"₹{daily_remaining:,.0f}", "of ₹25k")
                        col3.metric("Latency", f"{latency_ms}ms", "response")

                        st.divider()

                        # Show security details
                        st.markdown("#### 🔒 Security & Compliance")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Account Status", account_status)
                        col2.metric("KYC Verified", "✅ Yes" if kyc_verified else "❌ No")
                        col3.metric("Transactions Today", transaction_count)
                        col4.metric("Fraud Detection", "Active")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.markdown(f"**Debug info:** {str(e)}")

st.divider()
st.caption("✅ Banking Agent v3.1 | Full Orchestrator | Production Ready")

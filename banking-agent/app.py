"""
BANKING AGENT - STREAMLIT APP (SIMPLE)
Connects directly to your Databricks workspace

Installation:
    pip install streamlit databricks-sql-connector

Run locally:
    streamlit run app.py
"""

import streamlit as st
from databricks import sql
from datetime import datetime
import time

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="🏦 Banking Agent",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Banking Agent")
st.markdown("*Intelligent financial assistant for banking operations*")

# ============================================
# SIDEBAR - ENTER YOUR DATABRICKS INFO HERE
# ============================================

with st.sidebar:
    st.title("🔐 Databricks Connection")

    workspace_url = st.text_input(
        "Workspace URL",
        placeholder="https://adb-1234567890.azuredatabricks.net"
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
        with st.spinner("⏳ Processing..."):
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

                # Get user data
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

                    # Get daily transfers
                    cursor.execute(f"""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM banking_agent_db.realistic_transactions
                    WHERE user_id = '{user_id}'
                      AND DATE(timestamp) = CURRENT_DATE()
                      AND is_fraudulent = 0
                    """)

                    daily_used = float(cursor.fetchone()[0] or 0)
                    daily_limit = 25000
                    daily_remaining = daily_limit - daily_used

                    # Get fraud info
                    cursor.execute(f"""
                    SELECT COALESCE(COUNT(*), 0) as count
                    FROM banking_agent_db.realistic_transactions
                    WHERE user_id = '{user_id}' AND is_fraudulent = 1
                    """)

                    fraud_count = cursor.fetchone()[0] or 0
                    fraud_score = min(0.9, fraud_count * 0.15)
                    fraud_risk = "LOW ✓" if fraud_score < 0.3 else "MEDIUM ⚠️" if fraud_score < 0.7 else "HIGH 🚨"

                    # Simple response
                    if any(w in user_query.lower() for w in ['balance', 'how much']):
                        intent = "BALANCE"
                        response_text = f"Your balance is **₹{balance:,.2f}**. Daily limit: ₹{daily_limit:,}. Used: ₹{daily_used:,.2f}. Remaining: ₹{daily_remaining:,.2f}"
                    elif any(w in user_query.lower() for w in ['transfer', 'send', 'pay']):
                        intent = "TRANSACTION"
                        response_text = f"I can help with your transfer. Balance: ₹{balance:,.2f}. Daily remaining: ₹{daily_remaining:,.2f}. What amount?"
                    else:
                        intent = "POLICY"
                        response_text = "I can help with policy information. What would you like to know?"

                    latency_ms = int((time.time() - start_time) * 1000)

                    cursor.close()
                    connection.close()

                    # Display results
                    st.success("✅ Success!")

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {user_name} | ₹{balance:,.2f}")
                    with col2:
                        st.markdown(f"**{intent}**")

                    st.divider()
                    st.markdown("#### Question")
                    st.markdown(f"`{user_query}`")

                    st.divider()
                    st.markdown("#### Response")
                    st.markdown(response_text)

                    st.divider()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Fraud Risk", fraud_risk, f"{fraud_score:.1%}")
                    col2.metric("Daily Remaining", f"₹{daily_remaining:,.0f}", "of ₹25k")
                    col3.metric("Latency", f"{latency_ms}ms", "response")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.divider()
st.caption("✅ Banking Agent v3.1 | Production Ready")

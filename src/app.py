"""
Insurance Claim Agent - Streamlit UI
A professional interface for the insurance claim chatbot.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from agent import InsuranceClaimAgent
import json

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Apex Auto Assurance - Claims Portal",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1E3A5F;
        --secondary-color: #2E86AB;
        --accent-color: #F18F01;
        --success-color: #28A745;
        --warning-color: #FFC107;
        --danger-color: #DC3545;
        --light-bg: #F8F9FA;
        --dark-text: #212529;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E86AB 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }

    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }

    /* Message styling */
    .user-message {
        background: #E3F2FD;
        padding: 1rem 1.25rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.75rem 0;
        margin-left: 15%;
        border-left: 4px solid #2E86AB;
    }

    .assistant-message {
        background: #F8F9FA;
        padding: 1rem 1.25rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.75rem 0;
        margin-right: 15%;
        border-left: 4px solid #1E3A5F;
    }

    /* Sidebar styling */
    .sidebar-section {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .sidebar-section h3 {
        color: #1E3A5F;
        font-size: 1rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #F18F01;
    }

    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .status-active {
        background: #D4EDDA;
        color: #155724;
    }

    .status-pending {
        background: #FFF3CD;
        color: #856404;
    }

    .status-complete {
        background: #CCE5FF;
        color: #004085;
    }

    /* Info cards */
    .info-card {
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    .info-card-label {
        font-size: 0.75rem;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .info-card-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E3A5F;
    }

    /* Tier badges */
    .tier-simple {
        background: #6C757D;
        color: white;
    }

    .tier-advanced {
        background: #2E86AB;
        color: white;
    }

    .tier-premium {
        background: #F18F01;
        color: white;
    }

    /* Risk indicators */
    .risk-low {
        color: #28A745;
    }

    .risk-medium {
        color: #FFC107;
    }

    .risk-high {
        color: #DC3545;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E86AB 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }

    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #E9ECEF;
        padding: 0.75rem 1.25rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #2E86AB;
        box-shadow: 0 0 0 3px rgba(46, 134, 171, 0.1);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Conversation turn counter */
    .turn-counter {
        text-align: center;
        padding: 0.5rem;
        background: #E9ECEF;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #495057;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent" not in st.session_state:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            st.session_state.agent = InsuranceClaimAgent(api_key)
        else:
            st.session_state.agent = None

    if "claim_started" not in st.session_state:
        st.session_state.claim_started = False

    if "conversation_turn" not in st.session_state:
        st.session_state.conversation_turn = 0


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🚗 Apex Auto Assurance</h1>
        <p>Claims Processing Portal - Your trusted partner in insurance claims</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with claim information."""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-section">
            <h3>📋 Claim Status</h3>
        </div>
        """, unsafe_allow_html=True)

        # Conversation turns
        st.markdown(f"""
        <div class="turn-counter">
            Conversation Turn: {st.session_state.conversation_turn} / 10+
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Show claim context if available
        if st.session_state.agent and st.session_state.agent.get_claim_context():
            context = st.session_state.agent.get_claim_context()

            # Client Information
            if "client" in context:
                client = context["client"]
                st.markdown("### 👤 Client Information")

                tier_class = f"tier-{client.get('tier', 'simple').lower()}"
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-card-label">Name</div>
                    <div class="info-card-value">{client.get('name', 'N/A')}</div>
                </div>
                <div class="info-card">
                    <div class="info-card-label">Policy Number</div>
                    <div class="info-card-value">{client.get('policy_number', 'N/A')}</div>
                </div>
                <div class="info-card">
                    <div class="info-card-label">Tier</div>
                    <div class="info-card-value">
                        <span class="status-badge {tier_class}">{client.get('tier', 'N/A')}</span>
                    </div>
                </div>
                <div class="info-card">
                    <div class="info-card-label">Country</div>
                    <div class="info-card-value">{client.get('country', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Coverage Analysis
            if "coverage_analysis" in context:
                analysis = context["coverage_analysis"]
                st.markdown("### 📊 Coverage Analysis")

                covered_status = "✅ Covered" if analysis.get("covered") else "❌ Not Covered"
                covered_class = "status-active" if analysis.get("covered") else "status-pending"

                st.markdown(f"""
                <div class="info-card">
                    <div class="info-card-label">Coverage Status</div>
                    <div class="info-card-value">
                        <span class="status-badge {covered_class}">{covered_status}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if analysis.get("deductible"):
                    st.markdown(f"""
                    <div class="info-card">
                        <div class="info-card-label">Deductible</div>
                        <div class="info-card-value">{analysis.get('deductible')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Risk Assessment
            if "risk_assessment" in context:
                risk = context["risk_assessment"]
                st.markdown("### ⚠️ Risk Assessment")

                risk_level = risk.get("risk_level", "N/A")
                risk_class = f"risk-{risk_level.lower()}"

                st.markdown(f"""
                <div class="info-card">
                    <div class="info-card-label">Risk Level</div>
                    <div class="info-card-value {risk_class}">{risk_level}</div>
                </div>
                <div class="info-card">
                    <div class="info-card-label">Risk Score</div>
                    <div class="info-card-value">{risk.get('risk_score', 'N/A')}/100</div>
                </div>
                """, unsafe_allow_html=True)

            # Extracted Entities
            if "extracted_entities" in context:
                entities = context["extracted_entities"]
                has_entities = any(entities.get(k) for k in entities)

                if has_entities:
                    st.markdown("### 🔍 Extracted Information")

                    for key, values in entities.items():
                        if values:
                            label = key.replace("_", " ").title()
                            st.markdown(f"**{label}:** {', '.join(values)}")

        else:
            st.info("Start a conversation to see claim details here.")

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 New Claim", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_turn = 0
            if st.session_state.agent:
                st.session_state.agent.reset_conversation()
            st.rerun()

        # Help section
        st.markdown("---")
        st.markdown("### ℹ️ Need Help?")
        st.markdown("""
        - **Simple Tier**: Basic coverage
        - **Advanced Tier**: Standard comprehensive
        - **Premium Tier**: All-inclusive elite

        *Claims must be reported within 24 hours*
        """)


def render_chat():
    """Render the chat interface."""
    # Chat messages container
    chat_container = st.container()

    with chat_container:
        # Welcome message if no messages
        if not st.session_state.messages:
            st.markdown("""
            <div class="assistant-message">
                <strong>Claims Assistant</strong><br><br>
                Welcome to Apex Auto Assurance Claims Portal! 👋<br><br>
                I'm here to help you with your insurance claim. How can I assist you today?<br><br>
                You can:
                <ul>
                    <li>File a new claim</li>
                    <li>Check your coverage</li>
                    <li>Get information about your policy</li>
                    <li>Track an existing claim</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>Claims Assistant</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)

    # Chat input
    st.markdown("<br>", unsafe_allow_html=True)

    # Check for API key
    if not st.session_state.agent:
        st.error("⚠️ ANTHROPIC_API_KEY not found. Please set it in your environment variables or .env file.")
        api_key = st.text_input("Enter your Anthropic API Key:", type="password")
        if api_key:
            st.session_state.agent = InsuranceClaimAgent(api_key)
            st.rerun()
        return

    # Message input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.conversation_turn += 1

        # Get agent response
        with st.spinner("Processing your request..."):
            try:
                response = st.session_state.agent.chat(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

        st.rerun()


def main():
    """Main application entry point."""
    initialize_session_state()
    render_header()

    # Layout with sidebar
    render_sidebar()

    # Main chat area
    render_chat()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6C757D; font-size: 0.85rem;">
        <p>Apex Auto Assurance Claims Portal | Secure & Confidential</p>
        <p>For emergencies, call 1-800-APEX-HELP</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

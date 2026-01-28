"""
Insurance Claim Agent - Streamlit UI
A professional interface for the insurance claim chatbot.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import io
from PIL import Image
from dotenv import load_dotenv
from agent import InsuranceClaimAgent
import json

# Maximum image size in bytes (4MB to stay under 5MB API limit)
MAX_IMAGE_SIZE = 4 * 1024 * 1024
# Maximum image dimension
MAX_IMAGE_DIMENSION = 2048


def compress_image(image_bytes: bytes, media_type: str, max_size: int = MAX_IMAGE_SIZE) -> tuple[bytes, str]:
    """
    Compress and resize an image to fit within the size limit.

    Args:
        image_bytes: Original image bytes
        media_type: MIME type of the image
        max_size: Maximum size in bytes

    Returns:
        Tuple of (compressed_bytes, media_type)
    """
    # Open image with PIL
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA to RGB if necessary (for JPEG compression)
    if img.mode in ('RGBA', 'P'):
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if dimensions are too large
    width, height = img.size
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        ratio = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Compress with decreasing quality until under size limit
    quality = 85
    output_format = 'JPEG'
    output_media_type = 'image/jpeg'

    while quality > 10:
        buffer = io.BytesIO()
        img.save(buffer, format=output_format, quality=quality, optimize=True)
        compressed_bytes = buffer.getvalue()

        if len(compressed_bytes) <= max_size:
            return compressed_bytes, output_media_type

        # Reduce quality and try again
        quality -= 10

        # If still too large, also reduce dimensions
        if quality <= 50:
            width, height = img.size
            img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)

    # Final attempt with lowest quality
    buffer = io.BytesIO()
    img.save(buffer, format=output_format, quality=10, optimize=True)
    return buffer.getvalue(), output_media_type

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Apex Auto Assurance - Claims Portal",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling with improved fonts
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');

    /* Global font settings */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 16px;
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Main theme colors */
    :root {
        --primary-color: #0F2942;
        --secondary-color: #1A5F7A;
        --accent-color: #F59E0B;
        --accent-hover: #D97706;
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --danger-color: #EF4444;
        --light-bg: #F8FAFC;
        --dark-text: #1E293B;
        --muted-text: #64748B;
        --border-color: #E2E8F0;
        --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* Main content area - add margins to reduce content width */
    /* Try targeting the specific data-testid that Streamlit uses */
    [data-testid="stMainBlockContainer"] {
    max-width: 1200px !important;
    padding-left: 5rem !important;
    padding-right: 5rem !important;
    margin: 0 auto !important;
    }   

    /* Sidebar - add some padding */
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem !important;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0F2942 0%, #1A5F7A 50%, #0F2942 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 40px rgba(15, 41, 66, 0.3);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.5;
    }

    .header-content {
        position: relative;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }

    .header-logo {
        width: 64px;
        height: 64px;
        background: white;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .header-text h1 {
        margin: 0;
        font-family: 'Poppins', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .header-text p {
        margin: 0.25rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
        font-weight: 400;
    }

    .header-badge {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 500;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: var(--card-shadow);
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }

    /* Message styling */
    .message-container {
        margin: 1rem 0;
        animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-message {
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 20px 20px 8px 20px;
        margin: 1rem 0;
        margin-left: 10%;
        border: 1px solid #C7D2FE;
        position: relative;
    }

    .user-message::before {
        content: '';
        position: absolute;
        bottom: -1px;
        right: 20px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-top-color: #E0E7FF;
        border-bottom: 0;
        margin-bottom: -8px;
    }

    .assistant-message {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 20px 20px 20px 8px;
        margin: 1rem 0;
        margin-right: 10%;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    .message-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--dark-text);
    }

    .message-header .avatar {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
    }

    .user-avatar {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
    }

    .assistant-avatar {
        background: linear-gradient(135deg, #0F2942 0%, #1A5F7A 100%);
        color: white;
    }

    .message-content {
        font-size: 0.95rem;
        line-height: 1.7;
        color: var(--dark-text);
    }

    .message-content ul {
        margin: 0.75rem 0;
        padding-left: 1.5rem;
    }

    .message-content li {
        margin: 0.5rem 0;
    }

    /* Image in message */
    .message-image {
        margin-top: 1rem;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }

    .message-image img {
        max-width: 100%;
        max-height: 300px;
        object-fit: contain;
        display: block;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        padding: 1rem;
    }

    .sidebar-section {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 1px solid var(--border-color);
    }

    .sidebar-section h3 {
        font-family: 'Poppins', sans-serif;
        color: var(--primary-color);
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--accent-color);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Status indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.85rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    .status-active {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        color: #065F46;
    }

    .status-pending {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
    }

    .status-complete {
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
        color: #1E40AF;
    }

    /* Info cards - NON-CLICKABLE */
    .info-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        padding: 1rem 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        border: 1px solid var(--border-color);
        pointer-events: none;
        cursor: default;
    }

    .info-card-label {
        font-size: 0.7rem;
        color: var(--muted-text);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .info-card-value {
        font-size: 1rem;
        font-weight: 600;
        color: var(--dark-text);
    }

    /* Tier badges */
    .tier-simple {
        background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
        color: white;
    }

    .tier-advanced {
        background: linear-gradient(135deg, #1A5F7A 0%, #0F2942 100%);
        color: white;
    }

    .tier-premium {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
    }

    /* Risk indicators */
    .risk-low {
        color: #059669;
        font-weight: 600;
    }

    .risk-medium {
        color: #D97706;
        font-weight: 600;
    }

    .risk-high {
        color: #DC2626;
        font-weight: 600;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #0F2942 0%, #1A5F7A 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.75rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(15, 41, 66, 0.2);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(15, 41, 66, 0.3);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Conversation turn counter */
    .turn-counter {
        text-align: center;
        padding: 0.75rem 1rem;
        background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%);
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--muted-text);
        border: 1px solid var(--border-color);
        pointer-events: none;
    }

    .turn-count {
        font-weight: 700;
        color: var(--primary-color);
    }

    /* Welcome card - NON-CLICKABLE */
    .welcome-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
        pointer-events: none;
        margin-bottom: 2rem;
    }

    .welcome-title {
        font-family: 'Poppins', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--dark-text);
        margin-bottom: 1rem;
    }

    .welcome-subtitle {
        color: var(--muted-text);
        font-size: 1rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .feature-list {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }

    .feature-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        background: var(--light-bg);
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--dark-text);
        border: 1px solid var(--border-color);
        pointer-events: none;
    }

    .feature-icon {
        font-size: 1.25rem;
    }

    /* Footer styling */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: var(--muted-text);
        font-size: 0.85rem;
        border-top: 1px solid var(--border-color);
        margin-top: 2rem;
    }

    .footer-link {
        color: var(--secondary-color);
        text-decoration: none;
        font-weight: 500;
    }

    /* ============================================
       CHAT INPUT BOX - Card Style
       ============================================ */

    /* Input card - using Streamlit's border=True container */
    [data-testid="stVerticalBlock"]:has(> [data-testid="stVerticalBlockBorderWrapper"]) > [data-testid="stVerticalBlockBorderWrapper"] {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 16px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        margin-bottom: 1rem !important;
    }

    /* Reset all nested elements inside the bordered container */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stForm"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stForm"] > div,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stElementContainer"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] > div {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
        margin: 0 !important;
    }

    /* Remove any card styling from form wrapper */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
    }

    /* Full width text area */
    .stTextArea > div > div > textarea {
        background: #f4f4f4 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        font-weight: 400 !important;
        color: #0d0d0d !important;
        box-shadow: none !important;
        outline: none !important;
        width: 100% !important;
        resize: none !important;
        min-height: 40px !important;
        height: auto !important;
        line-height: 24px !important;
        font-family: inherit !important;
        overflow-y: hidden !important;
    }

    .stTextArea > div > div > textarea:focus {
        background: #ececec !important;
    }

    .stTextArea > div > div > textarea::placeholder {
        color: #8e8e8e !important;
        line-height: 24px !important;
    }

    .stTextArea > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        width: 100% !important;
    }

    /* Hide instructions text */
    .stTextArea [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Input row - upload button and text area side by side */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) {
        align-items: stretch !important;
        gap: 8px !important;
    }

    /* Upload button column - use flexbox to center button vertically within the row */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:first-child {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 44px !important;
    }

    /* Ensure all nested elements in button column also center */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:first-child > div,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:first-child > div > div,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:first-child .stButton {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Text area column - take remaining space */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:last-child {
        flex: 1 1 auto !important;
    }

    /* Upload button - transparent circular, centered via flexbox parent */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:first-child .stButton > button {
        background: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        min-height: 40px !important;
        padding: 0 !important;
        font-size: 20px !important;
        cursor: pointer !important;
        transition: background 0.15s ease !important;
        box-shadow: none !important;
        margin: 0 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"]:first-child .stButton > button:hover {
        background: #e2e8f0 !important;
        transform: none !important;
    }

    /* Uploaded Files Display - Modern Card Style */
    .uploaded-files-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        margin-top: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    .uploaded-files-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-weight: 600;
        font-size: 13px;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .uploaded-files-header span:first-child {
        font-size: 16px;
    }

    .uploaded-files-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .uploaded-file-item {
        display: flex;
        align-items: center;
        gap: 12px;
        background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 14px;
        color: #334155;
        transition: all 0.2s ease;
    }

    .uploaded-file-item:hover {
        border-color: #cbd5e1;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }

    .uploaded-file-thumbnail {
        width: 44px;
        height: 44px;
        border-radius: 8px;
        object-fit: cover;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }

    .uploaded-file-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .uploaded-file-name {
        font-weight: 500;
        color: #1e293b;
        max-width: 160px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 14px;
    }

    .uploaded-file-size {
        font-size: 12px;
        color: #94a3b8;
    }

    .uploaded-file-status {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #10b981;
        font-weight: 500;
        background: rgba(16, 185, 129, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
    }

    .uploaded-file-status span:first-child {
        font-size: 14px;
    }

    /* ============================================
       COLLAPSIBLE SECTIONS (Expanders)
       ============================================ */

    /* Welcome card expander styling */
    .stExpander {
        border: none !important;
        background: transparent !important;
        margin-bottom: 1rem !important;
    }

    .stExpander > details {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        overflow: hidden !important;
    }

    .stExpander > details > summary {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        color: #1e293b !important;
        padding: 1rem 1.25rem !important;
        background: white !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }

    .stExpander > details[open] > summary {
        border-bottom: 1px solid #e2e8f0 !important;
    }

    .stExpander > details > div {
        padding: 1rem 1.25rem !important;
        background: white !important;
    }

    /* Welcome content inside expander */
    .welcome-content {
        padding: 0.5rem 0 !important;
    }

    .welcome-content .welcome-subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .welcome-content .feature-list {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    .welcome-content .feature-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px;
        background: #f8fafc;
        border-radius: 10px;
        transition: all 0.2s ease;
    }

    .welcome-content .feature-item:hover {
        background: #f1f5f9;
        transform: translateX(4px);
    }

    .welcome-content .feature-icon {
        font-size: 1.2rem;
    }

    /* Uploaded files inside expander */
    .uploaded-file-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 14px;
        color: #334155;
    }

    /* ============================================
       FILE UPLOAD
       ============================================ */

    /* Hidden file uploader - invisible but clickable */
    [data-testid="stFileUploader"] {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }

    /* Keep the actual file input accessible for JS click */
    [data-testid="stFileUploader"] input[type="file"] {
        position: absolute !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
    }

    /* File chip buttons - styled as removable chips */
    [data-testid="stHorizontalBlock"]:has([data-testid="stButton"]):not(:has(.stTextArea)) [data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 4px !important;
    }

    /* Chip button styling - targets buttons with emoji pattern */
    [data-testid="stButton"] button[kind="secondary"] {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%) !important;
        border: 1px solid #a5b4fc !important;
        border-radius: 20px !important;
        padding: 6px 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #3730a3 !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        min-height: 32px !important;
        height: auto !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="stButton"] button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%) !important;
        border-color: #f87171 !important;
        color: #dc2626 !important;
        transform: none !important;
    }

    /* ============================================
       ATTACHED IMAGES SECTION
       ============================================ */

    .attached-images-container {
        margin-bottom: 8px;
    }

    /* Image chips row - fixed 4 columns with equal spacing */
    [data-testid="stVerticalBlock"]:has(.stTextArea) [data-testid="stHorizontalBlock"]:first-of-type {
        gap: 4px !important;
        justify-content: flex-start !important;
    }

    [data-testid="stVerticalBlock"]:has(.stTextArea) [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 2px !important;
    }

    /* Chat message images */
    .message-images {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }

    .message-images .chat-image {
        max-width: 200px;
        max-height: 150px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        object-fit: cover;
    }

    /* ============================================
       CHAT INPUT STYLING
       ============================================ */

    /* Style the chat input */
    [data-testid="stChatInput"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        background: white !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #f4f4f4 !important;
        border-radius: 12px !important;
    }

    /* Image chips - allow wrapping */
    [data-testid="stHorizontalBlock"]:first-of-type {
        flex-wrap: wrap !important;
    }

</style>
""", unsafe_allow_html=True)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


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

    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []

    if "input_key" not in st.session_state:
        st.session_state.input_key = 0


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <div class="header-left">
                <div class="header-logo">🚗</div>
                <div class="header-text">
                    <h1>Apex Auto Assurance</h1>
                    <p>Claims Processing Portal</p>
                </div>
            </div>
            <div class="header-badge">
                🔒 Secure Connection
            </div>
        </div>
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
            Conversation Turn: <span class="turn-count">{st.session_state.conversation_turn}</span> / 10+
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
            st.info("💡 Start a conversation to see claim details here.")

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 New Claim", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_turn = 0
            st.session_state.uploaded_images = []
            if st.session_state.agent:
                st.session_state.agent.reset_conversation()
            st.rerun()

        # Help section
        st.markdown("---")
        st.markdown("### ℹ️ Policy Tiers")
        st.markdown("""
        <div class="info-card">
            <div class="info-card-label">Simple</div>
            <div class="info-card-value" style="font-size: 0.85rem;">Basic liability coverage</div>
        </div>
        <div class="info-card">
            <div class="info-card-label">Advanced</div>
            <div class="info-card-value" style="font-size: 0.85rem;">Standard comprehensive</div>
        </div>
        <div class="info-card">
            <div class="info-card-label">Premium</div>
            <div class="info-card-value" style="font-size: 0.85rem;">All-inclusive elite</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption("📞 Emergency: 1-800-APEX-HELP")


def render_chat():
    """Render the chat interface."""
    # Chat messages container
    chat_container = st.container()

    with chat_container:
        # Welcome message - collapsible
        if not st.session_state.messages:
            with st.expander("👋 Welcome to Claims Assistant", expanded=True):
                st.markdown("""
                <div class="welcome-content">
                    <div class="welcome-subtitle">
                        I'm here to help you with your insurance claim. Upload photos of damage and describe your situation - I'll guide you through the entire process.
                    </div>
                    <div class="feature-list">
                        <div class="feature-item">
                            <span class="feature-icon">📝</span>
                            <span>File a new claim</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">🔍</span>
                            <span>Check your coverage</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">📸</span>
                            <span>Upload damage photos</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">📋</span>
                            <span>Track claim status</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                content_html = f"""
                <div class="message-container">
                    <div class="user-message">
                        <div class="message-header">
                            <span class="avatar user-avatar">👤</span>
                            <span>You</span>
                        </div>
                        <div class="message-content">{message.get("text", message.get("content", ""))}</div>
                """
                if "images" in message and message["images"]:
                    content_html += '<div class="message-images">'
                    for img_data in message["images"]:
                        content_html += f'<img src="data:image/png;base64,{img_data}" alt="Uploaded image" class="chat-image" />'
                    content_html += '</div>'
                content_html += "</div></div>"
                st.markdown(content_html, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-container">
                    <div class="assistant-message">
                        <div class="message-header">
                            <span class="avatar assistant-avatar">🤖</span>
                            <span>Claims Assistant</span>
                        </div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Check for API key
    if not st.session_state.agent:
        st.error("⚠️ ANTHROPIC_API_KEY not found. Please set it in your environment variables or .env file.")
        api_key = st.text_input("Enter your Anthropic API Key:", type="password")
        if api_key:
            st.session_state.agent = InsuranceClaimAgent(api_key)
            st.rerun()
        return

    # Initialize attached files state
    if "attached_files" not in st.session_state:
        st.session_state.attached_files = []

    # Initialize uploader visibility state
    if "show_file_uploader" not in st.session_state:
        st.session_state.show_file_uploader = False
    if "auto_open_picker" not in st.session_state:
        st.session_state.auto_open_picker = False

    # Initialize preserved text input (persists when attaching images)
    if "preserved_input_text" not in st.session_state:
        st.session_state.preserved_input_text = ""

    # Maximum images allowed
    MAX_IMAGES = 4

    # Show warning message if max images reached (above the input card)
    if st.session_state.get("max_images_warning", False):
        st.warning(f"⚠️ Maximum {MAX_IMAGES} images allowed. Additional images were not added.")
        st.session_state.max_images_warning = False

    # Placeholder for processing spinner (above the input card)
    processing_placeholder = st.empty()
    st.session_state._processing_placeholder = processing_placeholder

    # Input card container - wraps attached images, text input, and buttons
    input_card = st.container(border=True)
    with input_card:
        # Placeholder for attached images - can be cleared during processing
        attached_images_placeholder = st.empty()

        # Show attached images inside the placeholder
        if st.session_state.attached_files:
            with attached_images_placeholder.container():
                cols = st.columns(4)  # Fixed 4 columns
                for idx in range(4):
                    with cols[idx]:
                        if idx < len(st.session_state.attached_files):
                            file_data = st.session_state.attached_files[idx]
                            short_name = file_data["name"][:10] + "..." if len(file_data["name"]) > 10 else file_data["name"]
                            if st.button(f"🖼️ {short_name} ✕", key=f"remove_{idx}"):
                                st.session_state.attached_files.pop(idx)
                                st.rerun()

        # Row with upload button on left and text input on right
        btn_col, input_col = st.columns([0.07, 0.93])

        # Upload button (left side)
        with btn_col:
            upload_clicked = st.button("📷", key="camera_btn", help="Upload images")

        # Form for text input - Enter submits the form (right side)
        with input_col:
            with st.form(key=f"message_form_{st.session_state.input_key}", clear_on_submit=True):
                user_input = st.text_area(
                    "Message",
                    placeholder="Ask anything (Press Enter to send, Shift+Enter for new line)",
                    key=f"user_message_input_{st.session_state.input_key}",
                    label_visibility="collapsed",
                    height=40
                )

                # Hidden submit button (form submits on Enter)
                send_clicked = st.form_submit_button("Send", use_container_width=False)

    # Handle upload button click outside the container
    if upload_clicked:
        st.session_state.show_file_uploader = True
        st.session_state.auto_open_picker = True
        st.rerun()

    # Store placeholder reference for clearing during processing
    st.session_state._attached_images_placeholder = attached_images_placeholder

    # Inject CSS to hide the submit button and JavaScript to enable Enter to send
    st.markdown("""
    <style>
        /* Hide the form submit button */
        [data-testid="stForm"] [data-testid="stFormSubmitButton"] {
            position: absolute !important;
            left: -9999px !important;
            width: 1px !important;
            height: 1px !important;
            opacity: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # JavaScript to handle Enter key for form submission
    components.html("""
    <script>
    (function() {
        const parentDoc = window.parent.document;

        // Setup Enter to send
        function setupEnterToSend() {
            const textareas = parentDoc.querySelectorAll('[data-testid="stForm"] textarea');

            textareas.forEach(function(textarea) {
                // Only add listener if not already added
                if (textarea.dataset.enterListenerAdded) return;
                textarea.dataset.enterListenerAdded = 'true';

                textarea.addEventListener('keydown', function(e) {
                    // Enter key without Shift
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        e.stopPropagation();

                        // Find the submit button in the same form
                        const form = textarea.closest('[data-testid="stForm"]');
                        if (form) {
                            const submitBtn = form.querySelector('[data-testid="stFormSubmitButton"] button');
                            if (submitBtn) {
                                submitBtn.click();
                            }
                        }
                    }
                });
            });
        }

        // Run setup and also observe for dynamic changes
        setupEnterToSend();

        // Re-run on any DOM changes (Streamlit re-renders)
        const observer = new MutationObserver(setupEnterToSend);
        observer.observe(parentDoc.body, { childList: true, subtree: true });
    })();
    </script>
    """, height=0)

    # File uploader (always present but hidden by CSS)
    new_files = st.file_uploader(
        "Select images",
        type=["png", "jpg", "jpeg", "gif", "webp"],
        accept_multiple_files=True,
        key=f"image_uploader_{st.session_state.input_key}",
        label_visibility="collapsed"
    )

    # Auto-click the file input to open native file picker when camera button was clicked
    if st.session_state.show_file_uploader and st.session_state.auto_open_picker:
        st.session_state.auto_open_picker = False
        st.session_state.show_file_uploader = False  # Reset immediately to prevent re-trigger
        components.html("""
        <script>
        (function() {
            // Only run once - use a flag to prevent multiple triggers
            if (window.filePickerTriggered) return;
            window.filePickerTriggered = true;

            const parentDoc = window.parent.document;
            const fileInput = parentDoc.querySelector('input[type="file"]');

            if (fileInput) {
                fileInput.style.pointerEvents = 'auto';
                fileInput.click();
            }

            // Reset flag after a delay
            setTimeout(function() {
                window.filePickerTriggered = false;
            }, 1000);
        })();
        </script>
        """, height=0)

    # Process uploaded files (max 4 images)
    if new_files:
        files_added = 0
        for file in new_files:
            if len(st.session_state.attached_files) >= MAX_IMAGES:
                break
            file.seek(0)
            file_bytes = file.read()
            exists = any(f["name"] == file.name for f in st.session_state.attached_files)
            if not exists:
                st.session_state.attached_files.append({
                    "name": file.name,
                    "type": file.type,
                    "bytes": file_bytes
                })
                files_added += 1

        # Show warning if max images reached
        if len(st.session_state.attached_files) >= MAX_IMAGES:
            st.session_state.max_images_warning = True

        st.session_state.input_key += 1
        st.session_state.show_file_uploader = False
        st.rerun()

    # Process message when send button clicked and there's input
    if send_clicked and user_input:
        # Clear attached images from display immediately
        if "_attached_images_placeholder" in st.session_state:
            st.session_state._attached_images_placeholder.empty()

        # Process attached images from session state
        image_data = []
        if st.session_state.attached_files:
            for file_data in st.session_state.attached_files:
                bytes_data = file_data["bytes"]
                media_type = file_data["type"]
                if len(bytes_data) > MAX_IMAGE_SIZE:
                    bytes_data, media_type = compress_image(bytes_data, media_type)
                base64_image = base64.b64encode(bytes_data).decode("utf-8")
                image_data.append({"base64": base64_image, "media_type": media_type})

        # Clear attachments from session state
        st.session_state.attached_files = []
        st.session_state.input_key += 1

        # Add user message to state
        user_message = {
            "role": "user",
            "text": user_input,
            "content": user_input,
            "images": [img["base64"] for img in image_data] if image_data else []
        }
        st.session_state.messages.append(user_message)
        st.session_state.conversation_turn += 1

        # Show processing spinner above the input card
        with st.session_state._processing_placeholder:
            with st.spinner("🔄 Processing your request..."):
                try:
                    response = st.session_state.agent.chat_with_images(user_input, image_data)
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
    st.markdown("""
    <div class="footer">
        <p><strong>Apex Auto Assurance Claims Portal</strong> | Secure & Confidential</p>
        <p>Need immediate assistance? Call <span class="footer-link">1-800-APEX-HELP</span></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

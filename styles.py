import streamlit as st


def load_css():
    st.markdown("""
    <style>

        /* =========================
           MAIN PAGE
        ========================= */

        .stApp {
            background-color: #f7f9fc;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }


                /* =========================
           HEADER
        ========================= */

        .main-title {
            font-size: 44px;
            font-weight: 750;
            color: #172554;
            margin-bottom: 6px;
            letter-spacing: -1px;
        }

        .main-subtitle {
            font-size: 17px;
            color: #64748b;
            margin-bottom: 18px;
            max-width: 750px;
        }

        .status-badge {
            display: inline-block;
            background-color: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            border-radius: 20px;
            padding: 7px 15px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 30px;
        }

                /* =========================
           FILE UPLOADER
        ========================= */

        [data-testid="stFileUploader"] {
            background-color: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 14px;
            padding: 10px;
            transition: 0.2s ease;
        }

        [data-testid="stFileUploader"]:hover {
            border-color: #60a5fa;
            background-color: #f8fbff;
        }

        [data-testid="stFileUploaderDropzone"] {
            background-color: transparent;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] {
            color: #475569;
        }

                /* =========================
           METRIC CARDS
        ========================= */

        .metric-card {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
            min-height: 105px;
        }

        .metric-label {
            font-size: 13px;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 25px;
            font-weight: 750;
            color: #172554;
        }

        .metric-description {
            font-size: 12px;
            color: #94a3b8;
            margin-top: 4px;
        }

                /* =========================
           RESEARCH QUESTION
        ========================= */

        .question-title {
            font-size: 22px;
            font-weight: 700;
            color: #172554;
            margin-top: 30px;
            margin-bottom: 4px;
        }

        .question-description {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 24px;
        }

        .question-input {
            margin-top: 10px;
        }

        .search-card {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 22px;
            margin-top: 10px;
            margin-bottom: 24px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        }

        /* Question input */

        [data-testid="stTextInput"] input {
            border-radius: 10px;
            border: 1px solid #cbd5e1;
            padding: 12px;
            font-size: 15px;
        }

        [data-testid="stTextInput"] input:focus {
            border-color: #60a5fa;
            box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.15);
        }

        /* Search button */

        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            padding: 9px 18px;
        }

                /* =========================
           ANSWER SECTION
        ========================= */

        .answer-title {
            font-size: 22px;
            font-weight: 700;
            color: #172554;
            margin-top: 30px;
            margin-bottom: 6px;
        }

        .answer-description {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 16px;
        }

        .answer-card {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #2563eb;
            border-radius: 14px;
            padding: 22px;
            margin-top: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
            line-height: 1.7;
        }

        .answer-label {
            font-size: 12px;
            font-weight: 700;
            color: #2563eb;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

    </style>
    """, unsafe_allow_html=True)
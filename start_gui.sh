#!/usr/bin/env bash
# Forward port 8501 if you’re SSHing with -NL 8501:localhost:8501
export STREAMLIT_AUTOLAUNCH=1
source .venv/bin/activate
streamlit run streamlit_chat.py --server.port 8501

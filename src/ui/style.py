# bvc_cup/ui/style.py
import streamlit as st

def inject_css():
    st.markdown(
        """
        <style>
        .stApp {background-color: #fff;}
        h1, h2, h3 {color: #087650 !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
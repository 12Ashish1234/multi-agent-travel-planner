import streamlit as st
from datetime import datetime
import time

# Placeholder for the time display
placeholder = st.empty()

while True:
    current_time = datetime.now().strftime("%H:%M:%S")
    placeholder.text(f"Current Time: {current_time}")
    time.sleep(1)

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import matplotlib.pyplot as plt
import plotly.express as px
import time

# Google Sheets Setup
# Replace with your Google Sheets credentials JSON file
CREDENTIALS_FILE = 'credentials.json'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    # Replace with the name of your Google Sheet
    SPREADSHEET_NAME = 'Mood Tracker'
    try:
        spreadsheet = gc.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.sheet1
    except gspread.SpreadsheetNotFound:
        spreadsheet = gc.create(SPREADSHEET_NAME)
        worksheet = spreadsheet.sheet1
        worksheet.append_row(['Timestamp', 'Mood', 'Note'])
        st.info(f"Created a new Google Sheet named '{SPREADSHEET_NAME}'.")
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

# Streamlit App
st.title("Mood Tracker")

# Mood Input Form
with st.form("mood_form"):
    mood = st.selectbox("How are you feeling?", ["Happy", "Neutral", "Sad", "Excited", "Anxious", "Tired", "Other"])
    note = st.text_area("Any notes?", max_chars=200)
    submitted = st.form_submit_button("Log Mood")

    if submitted:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            worksheet.append_row([timestamp, mood, note])
            st.success("Mood logged!")
            # Force a rerun to update the chart immediately
            st.rerun()
        except Exception as e:
            st.error(f"Error writing to Google Sheets: {e}")

st.markdown("---")

# Data Display and Charting
st.subheader("Today's Moods")

def load_data():
    try:
        data = worksheet.get_all_values()
        if data:
            df = pd.DataFrame(data, columns=['Timestamp', 'Mood', 'Note'])
            print(df.columns)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            return df
        else:
            return pd.DataFrame(columns=['Timestamp', 'Mood', 'Note'])
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        return pd.DataFrame(columns=['Timestamp', 'Mood', 'Note'])

data_df = load_data()

if not data_df.empty:
    print(data_df)
    today = date.today()
    today_data = data_df[data_df['Timestamp'].dt.date == today]

    if not today_data.empty:
        mood_counts = today_data['Mood'].value_counts().reset_index()
        mood_counts.columns = ['Mood', 'Count']

        fig_plotly = px.bar(mood_counts, x='Mood', y='Count', title=f"Mood Distribution for {today.strftime('%Y-%m-%d')}")
        st.plotly_chart(fig_plotly)
    else:
        st.info("No mood data logged for today yet.")
else:
    st.info("No mood data available.")

st.markdown("---")

# Data Filtering and Grouping
st.subheader("Historical Mood Data")

group_by = st.selectbox("Group by:", ["Day", "None"])
filter_moods = st.multiselect("Filter by Mood:", data_df['Mood'].unique() if not data_df.empty else [])

filtered_df = data_df.copy()

if filter_moods:
    filtered_df = filtered_df[filtered_df['Mood'].isin(filter_moods)]

if group_by == "Day" and not filtered_df.empty:
    grouped_data = filtered_df.groupby(filtered_df['Timestamp'].dt.date)['Mood'].count().reset_index()
    grouped_data.columns = ['Date', 'Count']

    fig_grouped_plotly = px.bar(grouped_data, x='Date', y='Count', title="Mood Count Over Time")
    st.plotly_chart(fig_grouped_plotly)
elif not filtered_df.empty:
    st.dataframe(filtered_df)
else:
    st.info("No data to display based on the current filters.")

# Auto-Refresh
time.sleep(5) # Refresh every 5 seconds
st.rerun()

# UI Polish
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f4f4;
    }
    .st-eb { /* Form container */
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .st-c7 { /* Submit button */
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 5px;
        cursor: pointer;
    }
    .st-c7:hover {
        background-color: #45a049;
    }
    .streamlit-expander {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .streamlit-expander-header {
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
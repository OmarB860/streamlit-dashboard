# Omar Barakat
# MIS412 Python and AI
# Homework: Streamlit Data Dashboard with AI Analyst

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from google import genai

# load the api key from the env file
load_dotenv("env")
api_key = os.getenv("GEMINI_API_KEY")

# page setup
st.set_page_config(page_title="Global Health Dashboard", layout="wide")
st.title("Global Health Dashboard")
st.write("Compare COVID cases, deaths, and fatality rate between countries.")


# Functions

@st.cache_data
def load_data(file_name):
    """Loads the csv file and returns None if it can't find it."""
    try:
        df = pd.read_csv(file_name)
        return df
    except FileNotFoundError:
        return None


@st.cache_data
def clean_data(df):
    """Changes Date to a datetime, renames the columns, and adds fatality rate."""
    # change Date from text to a datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # rename columns to match the radio buttons
    df = df.rename(columns={"Confirmed": "Confirmed Cases", "Deaths": "Confirmed Deaths"})

    # fatality rate is deaths divided by cases times 100
    df["Fatality Rate"] = df["Confirmed Deaths"] / df["Confirmed Cases"] * 100
    return df


def plot_trends(df, metric):
    """Makes a plotly line chart with one line for each country."""
    fig = px.line(df, x="Date", y=metric, color="Country", title=metric + " Over Time")
    return fig


@st.cache_resource
def get_client(key):
    """Connects to Gemini once so it doesn't reconnect every rerun."""
    return genai.Client(api_key=key)


def get_ai_analysis(client, summary, avg_data, metric):
    """Sends the tables to Gemini and returns what it writes back."""
    # turn the tables into text so they can go in the prompt
    prompt = f"Here is the latest {metric} for each country:\n{summary.to_string(index=False)}\n\n"
    prompt += f"Here is the average new daily numbers for the last 7 days:\n{avg_data.to_string(index=False)}\n\n"
    prompt += "Write a short analysis (around 150 words) comparing these countries. "
    prompt += "Say which ones stand out and only use these numbers."

    response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
    return response.text


# Load the data

data = load_data("global_health_data.csv")

if data is None:
    st.error("Can't find global_health_data.csv. It needs to be in the same folder as the app.")
else:
    data = clean_data(data)
    country_list = data["Country"].unique()

    # Sidebar

    with st.sidebar:
        st.header("Filters")
        countries = st.multiselect("Choose 1 to 5 countries:", country_list, default=country_list[:3])
        metric = st.radio("Choose a metric:", ("Confirmed Cases", "Confirmed Deaths", "Fatality Rate"))

    # check that 1 to 5 countries are picked
    if len(countries) == 0:
        st.warning("Please pick at least one country.")
    elif len(countries) > 5:
        st.warning("Please pick 5 countries or less.")
    else:
        # only keep the countries that were picked
        selected_data = data[data["Country"].isin(countries)]

        # Section 1: Trend Chart

        st.header("Trends Over Time", divider="blue")

        first_day = data["Date"].min()
        last_day = data["Date"].max()

        # start and end date next to each other
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date:", first_day, min_value=first_day, max_value=last_day)
        with col2:
            end_date = st.date_input("End date:", last_day, min_value=first_day, max_value=last_day)

        # start date has to be before end date
        if start_date >= end_date:
            st.warning("Start date has to be before the end date.")
        else:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            # only keep the dates in the range
            date_data = selected_data[(selected_data["Date"] >= start_date) & (selected_data["Date"] <= end_date)]
            st.plotly_chart(plot_trends(date_data, metric))

        # get the numbers for Section 2 and 3

        # the data adds up over time so the last day has the totals
        latest_data = selected_data[selected_data["Date"] == last_day]
        summary = latest_data[["Country", metric]]

        # sort highest to lowest
        summary = summary.sort_values(metric, ascending=False)
        summary = summary.round(2)

        # make a copy for the table with commas or a % sign so it's easier to read
        table = summary.copy()
        if metric == "Fatality Rate":
            table[metric] = [f"{value:.2f}%" for value in summary[metric]]
        else:
            table[metric] = [f"{value:,}" for value in summary[metric]]

        # use cases if Confirmed Cases is picked, otherwise use deaths
        if metric == "Confirmed Cases":
            column = "Confirmed Cases"
        else:
            column = "Confirmed Deaths"

        averages = []
        for country in countries:
            # get the last 8 days for this country
            last_8 = selected_data[selected_data["Country"] == country].tail(8)
            # last day total minus the total from 7 days before, then divide by 7
            new_total = last_8[column].iloc[-1] - last_8[column].iloc[0]
            averages.append(new_total / 7)

        avg_data = pd.DataFrame({"Country": countries, "7 Day Average": averages})

        # Section 2 on the left, Section 3 on the right
        left, right = st.columns([2, 3])

        # Section 2: Summary Table
        with left:
            st.header("Summary Table", divider="green")
            st.write(f"Total **{metric}** as of **{last_day.date()}**")
            st.dataframe(table, hide_index=True)

        # Section 3: Comparative Analysis
        with right:
            st.header("7 Day Average", divider="orange")
            st.write(f"Average new **{column.lower()}** per day for the last 7 days.")
            st.bar_chart(avg_data, x="Country", y="7 Day Average")

        # Section 4: AI Analyst

        st.header("Ask the AI Analyst", divider="violet")
        st.write("Click the button to have Gemini write a summary of the countries you picked.")

        if st.button("Generate AI Analysis"):
            if api_key is None:
                st.warning("No API key found. Add GEMINI_API_KEY to the env file.")
            else:
                try:
                    client = get_client(api_key)
                    with st.spinner("Waiting for Gemini..."):
                        analysis = get_ai_analysis(client, summary, avg_data, metric)
                    st.info(analysis)
                except Exception as e:
                    st.error(f"Error getting the AI analysis: {e}")

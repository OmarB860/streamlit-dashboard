# Global Health Dashboard

MIS412 homework project. A Streamlit dashboard for comparing COVID cases, deaths, and fatality rate between countries.

Live app: https://omarb-health-dashboard.streamlit.app

## Features
- Pick 1 to 5 countries and a metric in the sidebar
- Line chart of the trend over time with a date range
- Summary table of totals sorted highest to lowest
- Bar chart of the 7 day average of new cases or deaths
- AI Analyst that uses Gemini to write a summary

## How to run
```
pip install -r requirements.txt
streamlit run app.py
```
Add your Gemini key to a file named `env`:
```
GEMINI_API_KEY=your_key_here
```

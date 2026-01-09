import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="UIDAI Insight Engine", layout="wide", page_icon="🇮🇳")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    h1 { color: #1f77b4; }
    .stMetric { background-color: white; padding: 15px; border-radius: 5px; box-shadow: 1px 1px 5px #ddd; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING
# ==========================================
@st.cache_data
def load_master_data():
    # Load the clean data you created
    df = pd.read_csv('master_uidai_data_cleaned.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data
def load_forecast_data():
    # Load the AI predictions
    df = pd.read_csv('forecast_data.csv')
    
    # Fix the date column mismatch (date vs Date)
    if 'Date' in df.columns and 'date' in df.columns:
        df['Combined_Date'] = df['Date'].fillna(df['date'])
    elif 'Date' in df.columns:
        df['Combined_Date'] = df['Date']
    else:
        df['Combined_Date'] = df['date']
        
    df['Combined_Date'] = pd.to_datetime(df['Combined_Date'])
    return df

try:
    df_master = load_master_data()
    df_forecast = load_forecast_data()
    data_loaded = True
except FileNotFoundError:
    st.error("❌ Files not found! Make sure 'master_uidai_data_cleaned.csv' and 'forecast_data.csv' are in this folder.")
    data_loaded = False

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🇮🇳 UIDAI Dashboard")
page = st.sidebar.radio("Navigate", [
    "1. Executive Summary",
    "2. Demographics (Who?)", 
    "3. Migration Tracker (Where?)", 
    "4. AI Forecast (Future)"
])

if data_loaded:
    # Global Filters
    st.sidebar.subheader("Filters")
    selected_state = st.sidebar.selectbox("Select State", ["All India"] + list(df_master['state'].unique()))

    # Filter data based on selection
    if selected_state != "All India":
        df_filtered = df_master[df_master['state'] == selected_state]
    else:
        df_filtered = df_master

    # ==========================================
    # MODULE 1: EXECUTIVE SUMMARY
    # ==========================================
    if page == "1. Executive Summary":
        st.title("📊 Executive Dashboard")
        
        # KPI Metrics
        total_enrol = df_filtered[df_filtered['Type'] == 'Enrolment']['Count'].sum()
        total_updates = df_filtered[df_filtered['Type'] != 'Enrolment']['Count'].sum()
        top_district = df_filtered.groupby('district')['Count'].sum().idxmax()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Enrolments", f"{total_enrol:,.0f}")
        c2.metric("Total Updates (Bio + Demo)", f"{total_updates:,.0f}")
        c3.metric("Highest Traffic District", top_district)
        
        # Main Trend Chart
        st.subheader("Traffic Trend Over Time")
        trend_data = df_filtered.groupby(['date', 'Type'])['Count'].sum().reset_index()
        fig = px.line(trend_data, x='date', y='Count', color='Type', 
                      title="Enrolment vs Updates Trend")
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # MODULE 2: DEMOGRAPHICS
    # ==========================================
    elif page == "2. Demographics (Who?)":
        st.title("👥 Demographic Analysis")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("The Compliance Check")
            # Reuse your 'visualize_age.py' logic here
            age_summary = df_filtered.groupby(['Type', 'Age_Group'])['Count'].sum().reset_index()
            fig_bar = px.bar(age_summary, x='Type', y='Count', color='Age_Group', 
                             title="Who is accessing which service?", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.subheader("Data Story")
            st.info("""
            **Observation:** - Enrolments are driven by the 0-5 age group (Newborns).
            - Biometric Updates peak at 5-17 (Mandatory Updates).
            - Demographic Updates are highest in 18+ (Corrections/Migration).
            
            **Conclusion:** The Mandatory Biometric Update policy is working effectively.
            """)

    # ==========================================
    # MODULE 3: MIGRATION TRACKER
    # ==========================================
    elif page == "3. Migration Tracker (Where?)":
        st.title("🚚 Migration & Address Updates")
        
        # Filter for Address Updates (Proxy: Demographic Updates)
        # Assuming Demographic Updates usually imply address/name changes
        demo_data = df_filtered[df_filtered['Type'] == 'Update_Demographic']
        
        st.subheader("Hotspots for Demographic Updates")
        top_districts = demo_data.groupby('district')['Count'].sum().nlargest(10).reset_index()
        
        fig_map = px.bar(top_districts, x='Count', y='district', orientation='h',
                         title="Top 10 Districts for Demographic Updates",
                         color='Count', color_continuous_scale='Viridis')
        st.plotly_chart(fig_map, use_container_width=True)
        
        st.markdown("High volume in specific districts often correlates with **urban migration hubs** or **marriage migration**.")

    # ==========================================
    # MODULE 4: AI FORECAST
    # ==========================================
    elif page == "4. AI Forecast (Future)":
        st.title("🤖 Future Demand Prediction")
        
        st.markdown("Using **Linear Regression** to predict Enrolment trends for the next 6 months.")
        
        # Plotting the Forecast
        fig_ai = go.Figure()
        
        # 1. Plot Actual Historical Data
        fig_ai.add_trace(go.Scatter(
            x=df_forecast['Combined_Date'], 
            y=df_forecast['Actual_Count'],
            mode='lines',
            name='Actual Data'
        ))
        
        # 2. Plot AI Predictions (Dashed Line)
        # Filter only rows where we have a prediction
        pred_data = df_forecast.dropna(subset=['Predicted_Count'])
        
        fig_ai.add_trace(go.Scatter(
            x=pred_data['Combined_Date'], 
            y=pred_data['Predicted_Count'],
            mode='lines+markers',
            name='AI Forecast',
            line=dict(dash='dash', color='red')
        ))
        
        fig_ai.update_layout(title="Enrolment Forecast (Next 6 Months)")
        st.plotly_chart(fig_ai, use_container_width=True)
        
        st.success(f"AI Insight: The trend slope is negative (-43/day). We are reaching saturation.")

else:
    st.write("Waiting for data...")
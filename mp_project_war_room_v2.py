import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import plotly.figure_factory as ff
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(
    page_title="MP Project War Room",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOGO ---
logo = Image.open("Logo.png")

# --- DATA ---
@st.cache_data
def load_data():
    df = pd.read_excel("Historical_Master_Full_Realistic_30Weeks_CLEANED.xlsx")
    df.columns = [col.strip() for col in df.columns]  # clean columns
    return df

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.image(logo, width=120)
    st.markdown("## MP Govt.")
    week_options = sorted(df["Week Number"].unique())
    selected_week = st.selectbox("Select Week", week_options, index=len(week_options)-1)
    lang = st.radio("Language / भाषा चुनें", ["English", "Hindi"], index=0)
    st.markdown("---")
    nav = st.radio("Go to section:", [
        "Executive Summary",
        "AI Project Chat & Insights",
        "Amrut 1.0",
        "Amrut 2.0",
        "PM Awas Yojana – Urban"
    ], index=0)

# --- FILTER DATA ---
df_week = df[df["Week Number"] == selected_week]

# --- PROJECT AGGREGATION ---
def aggregate_project_progress(df_week):
    proj_group = df_week.groupby(
        ["Project Name", "Project category", "Department", "Sub-department", "Department Head", "Expected Completion"]
    ).agg({"Completion %": "mean", "Status Flag": "last"}).reset_index()
    return proj_group

proj_summary = aggregate_project_progress(df_week)

# --- STATUS FLAG LOGIC (from % completion) ---
def derive_status_flag(row):
    if row["Completion %"] >= 99.9:
        return "Completed"
    elif row["Completion %"] >= 85:
        return "On Track"
    elif row["Completion %"] < 85 and pd.to_datetime(row["Expected Completion"]) < pd.Timestamp.today():
        return "Delayed"
    else:
        return "Paused"

proj_summary["Derived Status"] = proj_summary.apply(derive_status_flag, axis=1)

# --- HEADER INFO CARDS ---
def status_count(df, status):
    return df[df["Derived Status"] == status].shape[0]

st.markdown("""
    <style>
        .info-card {
            background: #fff; border-radius: 10px; box-shadow:0 2px 10px #d7e0e7;
            padding: 16px; text-align:center; font-size:1.2em; margin-bottom: 0.5rem;
        }
        .ontrack {background:#219E38;color:white}
        .delayed {background:#E9B100;color:white}
        .completed {background:#2866E0;color:white}
        .paused {background:#F77F1E;color:white}
        .outscope {background:#818B99;color:white}
    </style>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.markdown(f"<div class='info-card'><b>Total Projects</b><br>{proj_summary.shape[0]}</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='info-card ontrack'><b>{status_count(proj_summary,'On Track')}</b><br>On Track</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='info-card delayed'><b>{status_count(proj_summary,'Delayed')}</b><br>Delayed</div>", unsafe_allow_html=True)
col4.markdown(f"<div class='info-card completed'><b>{status_count(proj_summary,'Completed')}</b><br>Completed</div>", unsafe_allow_html=True)
col5.markdown(f"<div class='info-card paused'><b>{status_count(proj_summary,'Paused')}</b><br>Paused</div>", unsafe_allow_html=True)
col6.markdown(f"<div class='info-card outscope'><b>{status_count(proj_summary,'Out of Scope')}</b><br>Out of Scope</div>", unsafe_allow_html=True)

st.markdown("---")

# --- MAIN VISUALS ---
col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown("#### Project Progress by Status")
    fig = px.bar(
        proj_summary,
        x="Completion %",
        y="Project Name",
        color="Derived Status",
        color_discrete_map={
            "Completed": "#2866E0",
            "On Track": "#219E38",
            "Delayed": "#E9B100",
            "Paused": "#F77F1E",
            "Out of Scope": "#818B99"
        },
        orientation="h",
        hover_data=["Department", "Sub-department", "Project category", "Department Head", "Expected Completion"],
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.markdown("#### Status Distribution")
    pie_df = proj_summary["Derived Status"].value_counts().reset_index()
    pie_df.columns = ["Status", "Count"]
    fig2 = px.pie(
        pie_df, 
        names="Status", 
        values="Count",
        color="Status",
        color_discrete_map={
            "Completed": "#2866E0",
            "On Track": "#219E38",
            "Delayed": "#E9B100",
            "Paused": "#F77F1E",
            "Out of Scope": "#818B99"
        },
        hole=0.6
    )
    st.plotly_chart(fig2, use_container_width=True)


# --- PROJECT PROGRESS BY CATEGORY (Compact Grid UI) ---
st.markdown("<div style='font-size:2rem;font-weight:700;color:#2866E0;padding-bottom:0.5rem;'>Project Progress by Category</div>", unsafe_allow_html=True)
cat_order = ["Super Critical", "Critical", "Urgent", "Moderate"]
cat_cols = st.columns(4)
cat_colors = {
    "Completed": "#2866E0",
    "On Track": "#219E38",
    "Delayed": "#E9B100",
    "Paused": "#F77F1E",
    "Out of Scope": "#818B99"
}

for i, cat in enumerate(cat_order):
    with cat_cols[i]:
        st.markdown(f"<div style='font-size:1.4rem;font-weight:600;margin-bottom:0.3rem'>{cat}</div>", unsafe_allow_html=True)
        cat_df = proj_summary[proj_summary["Project category"] == cat]
        if cat_df.empty:
            st.info("No projects in this category.")
        else:
            fig_cat = px.bar(
                cat_df, 
                x="Completion %",
                y="Project Name",
                color="Derived Status",
                color_discrete_map=cat_colors,
                orientation="h",
                height=220,
                category_orders={"Derived Status": ["Completed", "On Track", "Delayed", "Paused", "Out of Scope"]}
            )
            fig_cat.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis_title=None,
                xaxis_title=None,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
                plot_bgcolor="#fff"
            )
            fig_cat.update_yaxes(tickfont=dict(size=11))
            st.plotly_chart(fig_cat, use_container_width=True)


# --- HEATMAP (Handle duplicates by aggregating again) ---
st.markdown("#### Department-wise Project Heatmap")
heat_df = proj_summary.groupby(["Department", "Project Name"])["Completion %"].mean().reset_index()
try:
    heat_pivot = heat_df.pivot(index="Department", columns="Project Name", values="Completion %")
    heat_pivot = heat_pivot.fillna(0)
    heatmap_fig = ff.create_annotated_heatmap(
        z=heat_pivot.values,
        x=list(heat_pivot.columns),
        y=list(heat_pivot.index),
        annotation_text=np.round(heat_pivot.values,1).astype(str),
        colorscale=[[0, "#f7fbff"], [0.2, "#E9B100"], [0.5, "#219E38"], [0.8, "#2866E0"], [1, "#1B2A34"]],
        showscale=True
    )
    st.plotly_chart(heatmap_fig, use_container_width=True)
except Exception as e:
    st.warning(f"Unable to render heatmap for this week: {e}")

# --- TIMELINE FOR SUPER CRITICAL ---
st.markdown("#### Timeline Trend: Super Critical Projects")
timeline_df = df[df["Project category"] == "Super Critical"]
if not timeline_df.empty:
    agg_tl = timeline_df.groupby(["Week Number", "Project Name"]).agg({"Completion %": "mean"}).reset_index()
    fig_tl = px.line(
        agg_tl, 
        x="Week Number",
        y="Completion %",
        color="Project Name",
        markers=True
    )
    st.plotly_chart(fig_tl, use_container_width=True)

st.markdown("---")
st.markdown("**Note:** All data and status are for demonstration purposes only.", unsafe_allow_html=True)

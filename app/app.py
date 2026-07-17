import sys
import os
import io

# Modify path to import modules from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import definitions and functions from plot_relative_abundance
from plot_relative_abundance import (
    load_data,
    collate_small_categories,
    PALETTES,
    OTHER_COLOR,
    get_colors,
)

# Custom premium styling for Streamlit
st.set_page_config(
    page_title="Interactive Stats Grapher",
    page_icon="📊",
    layout="wide",
)

# Safe retrieval of analytics password from Streamlit secrets
analytics_password = None
try:
    if "ANALYTICS_PASSWORD" in st.secrets:
        analytics_password = st.secrets["ANALYTICS_PASSWORD"]
except Exception:
    pass

import streamlit_analytics2 as streamlit_analytics
streamlit_analytics.start_tracking(unsafe_password=analytics_password)

# Check application authentication
def check_password():
    """Returns True if the user has entered the correct password."""
    # Retrieve the password from secrets
    app_password = None
    try:
        if "APP_PASSWORD" in st.secrets:
            app_password = st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    
    # If no password is set, bypass authentication
    if not app_password:
        return True

    # Check if already authenticated in session state
    if st.session_state.get("authenticated", False):
        return True

    # Render CSS style so header/subheader look good on login page too
    st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                color: #2E4057;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }
            .subheader {
                font-size: 1.2rem;
                color: #566E80;
                margin-bottom: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Render a beautiful password prompt
    st.markdown('<div class="main-header" style="text-align: center; margin-top: 5rem;">🔒 Secure Access Required</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader" style="text-align: center;">Please enter the password to unlock the Interactive Stats Grapher.</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            password_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Unlock")
            
            if submitted:
                if password_input == app_password:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
                    
    return False

if not check_password():
    streamlit_analytics.stop_tracking(unsafe_password=analytics_password)
    st.stop()

st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #2E4057;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .subheader {
            font-size: 1.2rem;
            color: #566E80;
            margin-bottom: 2rem;
        }
        .section-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #2A9D8F;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #E9C46A;
            padding-bottom: 0.3rem;
        }
        .stButton>button {
            background-color: #2A9D8F !important;
            color: white !important;
            border-radius: 6px;
            font-weight: 600;
            border: none;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #264653 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 Interactive Stats Grapher</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Upload your Excel spreadsheets and generate premium, publication-quality figures interactively.</div>', unsafe_allow_html=True)

# File Uploader
uploaded_file = st.file_uploader("Upload Excel Spreadsheet (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Resolve sheet names
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        
        # Two-column layout for main page configuration
        col_data, col_plot = st.columns([1, 2])
        
        with col_data:
            st.markdown('<div class="section-header">1. File Settings</div>', unsafe_allow_html=True)
            selected_sheet = st.selectbox("Select Sheet Name", options=sheet_names)
            
            # Read selected sheet
            df_raw = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            st.write("### Data Preview", df_raw.head(5))
            
            st.markdown('<div class="section-header">2. Column Mapping</div>', unsafe_allow_html=True)
            all_cols = list(df_raw.columns)
            
            label_col = st.selectbox(
                "Label Column (Taxon / Category names)",
                options=all_cols,
                index=0
            )
            
            # Identify numeric columns for defaults
            numeric_cols = [c for c in all_cols if pd.api.types.is_numeric_dtype(df_raw[c])]
            non_label_cols = [c for c in all_cols if c != label_col]
            default_val_cols = [c for c in non_label_cols if c in numeric_cols]
            if not default_val_cols:
                default_val_cols = non_label_cols
                
            val_cols = st.multiselect(
                "Value Columns (e.g. sample abundances)",
                options=non_label_cols,
                default=default_val_cols
            )
            
            st.markdown('<div class="section-header">3. Select Graph Type</div>', unsafe_allow_html=True)
            graph_type = st.radio(
                "Choose chart layout:",
                options=[
                    "Horizontal Stacked Bar Chart (Relative Abundance)",
                    "Grouped Bar Chart",
                    "Simple Pie Chart (First Selected Column)",
                    "Line Chart"
                ]
            )

        with col_plot:
            st.markdown('<div class="section-header">4. Configuration & Rendering</div>', unsafe_allow_html=True)
            
            # Sidebar / Config Panel inside the plotting area (expanded settings)
            with st.expander("🛠️ Customize Chart Aesthetics", expanded=True):
                c_title = st.text_input("Chart Title", value=f"{selected_sheet} Analysis" if selected_sheet else "Graph Title")
                
                c1, c2 = st.columns(2)
                with c1:
                    x_label = st.text_input("X-Axis Label", value="Relative abundance (%)" if "Relative" in graph_type else "Value")
                    y_label = st.text_input("Y-Axis Label", value="Samples" if "Horizontal" in graph_type else "Labels")
                    palette = st.selectbox("Color Palette", options=list(PALETTES.keys()), index=0)
                with c2:
                    width = st.slider("Figure Width (inches)", min_value=4.0, max_value=20.0, value=9.5, step=0.5)
                    height = st.slider("Figure Height (inches)", min_value=1.5, max_value=15.0, value=3.0 if "Horizontal" in graph_type else 5.0, step=0.5)
                    dpi = st.number_input("Output Resolution (DPI)", min_value=72, max_value=600, value=300, step=50)

                # Specialized configs based on graph type
                if graph_type == "Horizontal Stacked Bar Chart (Relative Abundance)":
                    threshold = st.slider(
                        "Collation Threshold (%)", 
                        min_value=0.0, 
                        max_value=10.0, 
                        value=1.0, 
                        step=0.5,
                        help="Categories with values below this threshold will be grouped into 'Other'."
                    )
                    bar_height = st.slider("Bar Height", min_value=0.2, max_value=1.0, value=0.6, step=0.05)
                
                show_legend = st.checkbox("Show Legend", value=True)
                if show_legend:
                    legend_cols = st.number_input("Legend Columns", min_value=1, max_value=10, value=4)

            # Data Preparation
            if not val_cols:
                st.warning("Please select at least one Value Column to plot.")
            else:
                # Prepare temporary copy of mapped columns
                df = df_raw[[label_col] + val_cols].copy()
                df = df.rename(columns={label_col: "label"})
                df["label"] = df["label"].astype(str).str.strip()

                # For Relative Abundance Stacked Bar: normalize and collate
                if graph_type == "Horizontal Stacked Bar Chart (Relative Abundance)":
                    # Normalize columns to 0-100 scale (percentages)
                    for col in val_cols:
                        total_sum = pd.to_numeric(df[col], errors="coerce").sum()
                        if total_sum > 0:
                            # Auto-detect scale (0-1 vs 0-100) and normalize to percent
                            first_vals = pd.to_numeric(df[col], errors="coerce")
                            if first_vals.sum() <= 1.5:
                                df[col] = pd.to_numeric(df[col], errors="coerce") * 100
                            else:
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                    
                    df_processed = collate_small_categories(df, val_cols, threshold)
                else:
                    df_processed = df.copy()

                # Matplotlib Plotting
                fig, ax = plt.subplots(figsize=(width, height))
                
                # Retrieve palettes & colors
                colors = get_colors(df_processed["label"].tolist(), palette)
                
                # Check Graph Types and Plot
                if graph_type == "Horizontal Stacked Bar Chart (Relative Abundance)":
                    labels = df_processed["label"].tolist()
                    n_samples = len(val_cols)
                    sample_names = [str(c) for c in val_cols]
                    
                    y_pos = np.arange(n_samples)
                    left = np.zeros(n_samples)
                    
                    for i, (label, color) in enumerate(zip(labels, colors)):
                        vals = df_processed.loc[i, val_cols].to_numpy(dtype=float)
                        ax.barh(
                            y_pos,
                            vals,
                            left=left,
                            height=bar_height,
                            color=color,
                            edgecolor="white",
                            linewidth=0.6,
                            label=label
                        )
                        left += vals
                        
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(sample_names)
                    ax.set_xlabel(x_label)
                    ax.set_ylabel(y_label)
                    ax.set_xlim(0, 100)
                    ax.invert_yaxis()
                    
                    # Clean publication layout
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)
                    ax.spines["left"].set_visible(False)
                    ax.tick_params(axis="y", length=0)
                    ax.set_axisbelow(True)
                    ax.xaxis.grid(True, linewidth=0.4, alpha=0.4)
                    
                    if show_legend:
                        ncol = legend_cols
                        # Determine legend vertical offset based on height
                        legend_y = -0.3 - (0.15 / height)
                        ax.legend(
                            loc="upper center",
                            bbox_to_anchor=(0.5, legend_y),
                            ncol=ncol,
                            frameon=False,
                            fontsize=8,
                            handlelength=1.0,
                            handleheight=1.0,
                        )

                elif graph_type == "Grouped Bar Chart":
                    x_indices = np.arange(len(df_processed))
                    group_width = 0.8 / len(val_cols)
                    
                    for idx, col in enumerate(val_cols):
                        ax.bar(
                            x_indices + (idx * group_width) - (0.4) + (group_width / 2),
                            df_processed[col],
                            width=group_width,
                            label=col,
                            color=PALETTES[palette][idx % len(PALETTES[palette])]
                        )
                    ax.set_xticks(x_indices)
                    ax.set_xticklabels(df_processed["label"], rotation=45, ha="right")
                    ax.set_xlabel(x_label)
                    ax.set_ylabel(y_label)
                    
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)
                    ax.yaxis.grid(True, linewidth=0.4, alpha=0.4)
                    
                    if show_legend:
                        ax.legend(loc="best", frameon=False)

                elif graph_type == "Simple Pie Chart (First Selected Column)":
                    col_to_plot = val_cols[0]
                    wedges, texts, autotexts = ax.pie(
                        df_processed[col_to_plot],
                        labels=df_processed["label"],
                        autopct="%1.1f%%",
                        colors=colors,
                        wedgeprops=dict(width=0.6, edgecolor='w') # Donut shape
                    )
                    plt.setp(autotexts, size=8, weight="bold")
                    plt.setp(texts, size=8)
                    ax.set_title(f"{col_to_plot} Distribution", fontsize=12, fontweight="bold")
                    
                    if show_legend:
                        ax.legend(
                            df_processed["label"],
                            title=label_col,
                            loc="center left",
                            bbox_to_anchor=(1, 0, 0.5, 1),
                            frameon=False
                        )

                elif graph_type == "Line Chart":
                    for idx, col in enumerate(val_cols):
                        ax.plot(
                            df_processed["label"],
                            df_processed[col],
                            marker="o",
                            linewidth=2,
                            label=col,
                            color=PALETTES[palette][idx % len(PALETTES[palette])]
                        )
                    ax.set_xlabel(x_label)
                    ax.set_ylabel(y_label)
                    plt.xticks(rotation=45, ha="right")
                    
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)
                    ax.yaxis.grid(True, linewidth=0.4, alpha=0.4)
                    
                    if show_legend:
                        ax.legend(loc="best", frameon=False)

                if c_title:
                    ax.set_title(c_title, fontsize=14, fontweight="bold", pad=15)
                
                # Render inside Streamlit
                st.pyplot(fig)
                
                # Download Image Buffer
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
                buf.seek(0)
                
                st.download_button(
                    label="📥 Download Chart as PNG",
                    data=buf,
                    file_name=f"{c_title.replace(' ', '_').lower()}.png",
                    mime="image/png"
                )
                
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        st.info("Ensure the file contains valid headers and columns mapped properly.")
else:
    # Display beautiful placeholder/instructions
    st.info("💡 Please upload an Excel spreadsheet file to get started.")
    st.markdown("""
        ### Expected Excel Formats:
        - **Label Column**: Typically the first column, listing taxon or category labels (e.g. *Bacteroidia*, *Clostridia*).
        - **Value Columns**: One or more columns with numeric values representing abundance fractions (e.g. `0.23`) or percentages (e.g. `23.0`).
        
        The app will automatically detect percentage vs. fraction values and allow interactive threshold tuning.
    """)

streamlit_analytics.stop_tracking(unsafe_password=analytics_password)

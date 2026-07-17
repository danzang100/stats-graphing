# Stats Graphing and Interactive Plotting Application

This repository provides tools to clean, analyze, and plot relative abundance and general statistics datasets. It includes a command-line script for automated plotting and an interactive Streamlit application.

---

## Features

1. **Interactive Streamlit Interface**:
   - File Uploader: Load spreadsheet files (.xlsx).
   - Sheet Selector: Easily switch between workbook sheets.
   - Column Mapping: Select label and numerical value columns.
   - Multiple Graph Layouts: Horizontal Stacked Bar Charts (Relative Abundance), Grouped Bar Charts, Simple Pie Charts, and Line Charts.
   - Custom Aesthetics Panel: Customize chart titles, axis labels, dimensions, color palettes, DPI, and legends.
   - Download Utility: Export high-resolution PNG charts.
2. **Access Control**:
   - General application access is protected by a password gate.
3. **Usage Analytics**:
   - Embedded analytics tracked using streamlit-analytics2, locked behind a secondary administrator password dashboard.

---

## Streamlit Cloud Deployment

The application is deployed on Streamlit Community Cloud at:
https://stats-graphing.streamlit.app

### Steps to Use the Cloud Application

1. **Open the App**:
   Navigate to the URL: https://stats-graphing.streamlit.app

2. **Unlock the App**:
   - A password gate is active. Enter the secure application password configured in the app secrets to unlock the workspace.

3. **Upload Your File**:
   - Click the file uploader and choose a compatible Excel spreadsheet (.xlsx).
   - The file should ideally contain taxons, categories, or identifiers in one column (e.g. OTU IDs), and numeric counts or abundance percentages in other columns.

4. **Map Your Fields**:
   - Choose the sheet containing the target data.
   - Under Column Mapping, select the Label Column and the Value Columns.

5. **Choose Chart and Configure**:
   - Select a chart type from the options.
   - Expand the Customize Chart Aesthetics section to set titles, dimensions, resolutions, and choose from publication-friendly color palettes (e.g. teal_sand, colorblind-safe, earthy).

6. **Regenerate & Download**:
   - Tweak sliders and fields to automatically regenerate the plot.
   - Click Download Chart as PNG to retrieve a high-resolution version of the graph.

---

## Local Setup and Installation

### Prerequisites

Ensure you have Python 3.10+ installed.

### 1. Clone and Install Dependencies

Initialize a virtual environment and install the required libraries:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 2. Configure Local Secrets

To run the app locally with password gates enabled, create a secrets file inside the project directory:

Path: `.streamlit/secrets.toml`
```toml
ANALYTICS_PASSWORD = "admin"
APP_PASSWORD = "graph_password"
```

---

## Local Run Instructions

### Run the Interactive App

Launch the local Streamlit server:

```bash
streamlit run app/app.py
```

- Open `http://localhost:8501` in your browser.
- Log in using the `APP_PASSWORD` value.
- To view the administrator analytics dashboard, navigate to `http://localhost:8501/?analytics=on` and log in using the `ANALYTICS_PASSWORD`.

### Run the CLI Plotting Tool

You can also run the backend plotting script directly from your terminal:

```bash
python plot_relative_abundance.py "inputs/Classes Rel. Abun.xlsx"
```

- By default, output images are saved under `graphs/relative_abundance.png`.
- Run `python plot_relative_abundance.py --help` to see list of options (e.g. threshold filters, choosing palettes).
- Output in PDF format has been deprecated. Save outputs as PNG or SVG instead.

---

## Directory Structure

- `app/`
  - `app.py`: The Streamlit interactive application.
- `inputs/`: Standard folder to hold your Excel spreadsheets.
- `graphs/`: Folder where CLI output graphs are saved.
- `plot_relative_abundance.py`: The command-line utility.
- `requirements.txt`: List of required Python dependencies.
- `.gitignore`: Excludes caches, environment files, local inputs, output graphs, and secrets.

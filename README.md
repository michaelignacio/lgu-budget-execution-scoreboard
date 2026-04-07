# LGU Budget Execution Scorecard

A Streamlit dashboard for analyzing Local Government Unit (LGU) fiscal performance in the Philippines using Bureau of Local Government Finance (BLGF) data.

## What It Does

This app transforms raw BLGF Statement of Receipts and Expenditures data into actionable intelligence:

- **Execution Rate Analysis** — Shows how well LGUs are spending their budgets
- **Fiscal Health Monitoring** — Identifies surplus/deficit positions
- **NTA Dependency Tracking** — Measures reliance on national government transfers
- **Sector Spending Breakdown** — Visualizes allocation to Education, Health, and Economic Services
- **LGU Comparison** — Side-by-side comparison of two LGUs
- **Regional/Provincial Filters** — Drill down to specific areas including BARMM

## Data Source

Bureau of Local Government Finance (BLGF) — Statement of Receipts and Expenditures FY 2024

## How to Run

### Setup (First Time)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install streamlit pandas numpy plotly
```

### Run the App

```bash
source venv/bin/activate && streamlit run app.py
```

The app will open at http://localhost:8501

## Features

- **Overview Dashboard** — Summary statistics and distribution charts
- **LGU Scorecards** — Individual municipality/city fiscal performance cards
- **Search & Filter** — Find specific LGUs by name, region, or province
- **Compare Mode** — Compare two LGUs side-by-side
- **Export** — Download filtered data as CSV
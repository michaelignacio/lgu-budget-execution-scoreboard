"""
LGU Budget Data Processor
Cleans and transforms BLGF Statement of Receipts and Expenditures data
"""

import pandas as pd
import numpy as np


def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Load and clean the LGU budget data from CSV.
    
    Args:
        filepath: Path to sheet 1.csv
        
    Returns:
        Cleaned DataFrame with calculated metrics
    """
    # Load CSV, skip header rows (rows 1-11 contain metadata)
    df = pd.read_csv(filepath, skiprows=11, header=None, low_memory=False)
    
    # Define column names based on the structure
    columns = [
        'blank', 'region', 'province', 'lgu_name', 'lgu_type',
        'rpt_general', 'rpt_sef', 'rpt_total', 'tax_business', 'other_taxes',
        'total_tax_revenue', 'regulatory_fees', 'service_charges', 
        'economic_enterprises', 'other_receipts', 'total_non_tax',
        'total_local_sources', 'nta', 'other_shares_ntc', 'inter_local',
        'extraordinary', 'total_external', 'total_income',
        'general_public_services', 'education', 'health', 'labor', 
        'housing', 'social_welfare', 'total_social_services',
        'economic_services', 'debt_service_interest', 'total_expenditures',
        'net_operating', 'sale_assets', 'sale_debt', 'collection_loans',
        'total_capital_receipts', 'acquisition_loans', 'issuance_bonds',
        'total_loan_receipts', 'other_non_income', 'total_non_income',
        'capital_outlay', 'purchase_debt', 'grant_loans', 
        'total_capital_exp', 'loan_amortization', 'retirement_bonds',
        'total_debt_principal', 'other_non_operating', 'total_non_operating',
        'net_increase_funds', 'cash_beginning', 'fund_available',
        'prior_year_payable', 'continuing_appropriation', 'fund_end'
    ]
    
    # Assign column names (truncate to available columns)
    df.columns = columns[:len(df.columns)]
    
    # Remove any completely empty rows
    df = df.dropna(subset=['region', 'province', 'lgu_name'], how='all')
    
    # Clean string columns
    for col in ['region', 'province', 'lgu_name', 'lgu_type']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Convert numeric columns (handle commas and convert to float)
    numeric_cols = [
        'total_income', 'total_expenditures', 'total_social_services',
        'education', 'health', 'economic_services', 'nta', 'net_operating',
        'general_public_services', 'total_local_sources', 'total_external'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # Calculate key metrics
    df = calculate_metrics(df)
    
    # Add BARMM flag
    df['is_barmm'] = df['region'].str.contains('BARMM|Bangsamoro', case=False, na=False)
    
    return df


def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate key fiscal metrics for each LGU.
    """
    # Execution rate: expenditures / income (as percentage)
    df['execution_rate'] = (df['total_expenditures'] / df['total_income'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # NTA Dependency: NTA as % of total income
    df['nta_dependency'] = (df['nta'] / df['total_income'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Local revenue ratio
    df['local_revenue_ratio'] = (df['total_local_sources'] / df['total_income'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Social services as % of expenditures
    df['social_services_pct'] = (df['total_social_services'] / df['total_expenditures'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Education as % of expenditures
    df['education_pct'] = (df['education'] / df['total_expenditures'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Health as % of expenditures
    df['health_pct'] = (df['health'] / df['total_expenditures'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Economic services as % of expenditures
    df['economic_pct'] = (df['economic_services'] / df['total_expenditures'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Fiscal health category
    df['fiscal_health'] = df['net_operating'].apply(categorize_fiscal_health)
    
    # Execution category for color coding
    df['execution_category'] = df['execution_rate'].apply(categorize_execution)
    
    return df


def categorize_fiscal_health(value):
    """Categorize fiscal health based on net operating income."""
    if pd.isna(value):
        return 'Unknown'
    elif value > 0:
        return 'Surplus'
    elif value < 0:
        return 'Deficit'
    else:
        return 'Balanced'


def categorize_execution(rate):
    """Categorize execution rate for color coding."""
    if pd.isna(rate):
        return 'Unknown'
    elif rate >= 90:
        return 'High'
    elif rate >= 70:
        return 'Moderate'
    else:
        return 'Low'


def get_insights(row):
    """Generate automated insights for an LGU."""
    insights = []
    
    # Execution insight
    if row['execution_rate'] < 70:
        insights.append(f"Low execution rate ({row['execution_rate']:.1f}%) - potential bottlenecks")
    elif row['execution_rate'] > 100:
        insights.append(f"High execution ({row['execution_rate']:.1f}%) - may indicate deficit spending")
    
    # NTA dependency
    if row['nta_dependency'] > 80:
        insights.append(f"High NTA dependency ({row['nta_dependency']:.1f}%) - limited fiscal autonomy")
    elif row['nta_dependency'] < 50:
        insights.append(f"Strong local revenue ({row['nta_dependency']:.1f}% NTA dependency)")
    
    # Health spending
    if row['health_pct'] < 5:
        insights.append(f"Low health allocation ({row['health_pct']:.1f}%) - below typical benchmark")
    
    # Fiscal health
    if row['fiscal_health'] == 'Deficit':
        insights.append("Operating deficit - expenditures exceed income")
    elif row['fiscal_health'] == 'Surplus':
        insights.append("Operating surplus - healthy fiscal position")
    
    return insights


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Generate summary statistics for the dashboard."""
    return {
        'total_lgus': len(df),
        'avg_execution': df['execution_rate'].mean(),
        'high_execution': len(df[df['execution_category'] == 'High']),
        'low_execution': len(df[df['execution_category'] == 'Low']),
        'avg_nta_dependency': df['nta_dependency'].mean(),
        'surplus_count': len(df[df['fiscal_health'] == 'Surplus']),
        'deficit_count': len(df[df['fiscal_health'] == 'Deficit']),
    }

"""
LGU Budget Execution Scorecard
Streamlit app for visualizing LGU fiscal performance
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import load_and_clean_data, get_insights, get_summary_stats, SPREADSHEET_COLUMNS

# Page configuration
st.set_page_config(
    page_title="LGU Budget Execution Scorecard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .scorecard {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #1f4e79;
        margin-bottom: 20px;
    }
    .metric-high { color: #28a745; font-weight: bold; }
    .metric-moderate { color: #ffc107; font-weight: bold; }
    .metric-low { color: #dc3545; font-weight: bold; }
    .metric-label {
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .insight-box {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 10px 15px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
    }
    .insight-warning {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .insight-danger {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)


def get_execution_color(category):
    """Return color based on execution category."""
    colors = {
        'High': '#28a745',
        'Moderate': '#ffc107',
        'Low': '#dc3545',
        'Unknown': '#6c757d'
    }
    return colors.get(category, '#6c757d')


def format_currency(value):
    """Format value in millions with proper units."""
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 1000:
        return f"₱{value/1000:.2f}B"
    else:
        return f"₱{value:.2f}M"


@st.cache_data
def load_data():
    """Load and cache the data."""
    return load_and_clean_data('sheet 1.csv')


def main():
    # Header
    st.markdown('<div class="main-header">📊 LGU Budget Execution Scorecard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">FY 2024 Fiscal Performance Dashboard | Bureau of Local Government Finance Data</div>', unsafe_allow_html=True)
    
    # Load data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Region filter
    regions = ['All'] + sorted(df['region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Region", regions)
    
    # Filter by region first
    if selected_region != 'All':
        df_filtered = df[df['region'] == selected_region]
    else:
        df_filtered = df.copy()
    
    # Province filter (dynamic based on region)
    provinces = ['All'] + sorted(df_filtered['province'].unique().tolist())
    selected_province = st.sidebar.selectbox("Province", provinces)
    
    if selected_province != 'All':
        df_filtered = df_filtered[df_filtered['province'] == selected_province]
    
    # LGU Type filter
    lgu_types = ['All'] + sorted(df_filtered['lgu_type'].unique().tolist())
    selected_lgu_type = st.sidebar.selectbox("LGU Type", lgu_types)
    
    if selected_lgu_type != 'All':
        df_filtered = df_filtered[df_filtered['lgu_type'] == selected_lgu_type]
    
    # BARMM filter
    barmm_option = st.sidebar.radio("BARMM LGUs", ["All", "BARMM Only", "Non-BARMM"])
    if barmm_option == "BARMM Only":
        df_filtered = df_filtered[df_filtered['is_barmm'] == True]
    elif barmm_option == "Non-BARMM":
        df_filtered = df_filtered[df_filtered['is_barmm'] == False]
    
    # LGU Name search
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Search")
    
    search_term = st.sidebar.text_input("Search LGU/City/Municipality", "")
    if search_term:
        df_filtered = df_filtered[
            df_filtered['lgu_name'].str.contains(search_term, case=False, na=False) |
            df_filtered['province'].str.contains(search_term, case=False, na=False)
        ]
    
    # Execution rate filter
    st.sidebar.markdown("---")
    execution_filter = st.sidebar.multiselect(
        "Execution Rate",
        ['High (≥90%)', 'Moderate (70-90%)', 'Low (<70%)'],
        default=['High (≥90%)', 'Moderate (70-90%)', 'Low (<70%)']
    )
    
    # Map filter to categories
    execution_map = {
        'High (≥90%)': 'High',
        'Moderate (70-90%)': 'Moderate',
        'Low (<70%)': 'Low'
    }
    selected_categories = [execution_map[f] for f in execution_filter]
    df_filtered = df_filtered[df_filtered['execution_category'].isin(selected_categories)]
    
    # LGU Comparison Feature
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ Compare LGUs")
    
    compare_mode = st.sidebar.checkbox("Enable Comparison Mode")
    
    if compare_mode:
        # Get list of all LGUs for selection
        all_lgus = sorted(df['lgu_name'].unique().tolist())
        
        col_compare1, col_compare2 = st.sidebar.columns(2)
        
        with col_compare1:
            lgu1 = st.selectbox("LGU 1", all_lgus, key="lgu1")
        
        with col_compare2:
            lgu2 = st.selectbox("LGU 2", all_lgus, index=min(1, len(all_lgus)-1), key="lgu2")
        
        if lgu1 and lgu2 and lgu1 != lgu2:
            row1 = df[df['lgu_name'] == lgu1].iloc[0]
            row2 = df[df['lgu_name'] == lgu2].iloc[0]
            
            st.header("⚖️ LGU Comparison")
            
            # Comparison table with exact spreadsheet headings
            compare_data = {
                'Item': [
                    SPREADSHEET_COLUMNS['lgu_name'],
                    SPREADSHEET_COLUMNS['province'],
                    SPREADSHEET_COLUMNS['region'],
                    SPREADSHEET_COLUMNS['lgu_type'],
                    'Execution Rate (Calculated)',
                    'Fiscal Health (Calculated)',
                    'NTA Dependency (Calculated)',
                    SPREADSHEET_COLUMNS['total_income'],
                    SPREADSHEET_COLUMNS['total_expenditures'],
                    SPREADSHEET_COLUMNS['net_operating'],
                    f"{SPREADSHEET_COLUMNS['education']} (% of Expenditures)",
                    f"{SPREADSHEET_COLUMNS['health']} (% of Expenditures)",
                    f"{SPREADSHEET_COLUMNS['economic_services']} (% of Expenditures)"
                ],
                lgu1: [
                    row1['lgu_name'], row1['province'], row1['region'], row1['lgu_type'],
                    f"{row1['execution_rate']:.1f}%", row1['fiscal_health'], f"{row1['nta_dependency']:.1f}%",
                    format_currency(row1['total_income']), format_currency(row1['total_expenditures']),
                    format_currency(row1['net_operating']), f"{row1['education_pct']:.1f}%",
                    f"{row1['health_pct']:.1f}%", f"{row1['economic_pct']:.1f}%"
                ],
                lgu2: [
                    row2['lgu_name'], row2['province'], row2['region'], row2['lgu_type'],
                    f"{row2['execution_rate']:.1f}%", row2['fiscal_health'], f"{row2['nta_dependency']:.1f}%",
                    format_currency(row2['total_income']), format_currency(row2['total_expenditures']),
                    format_currency(row2['net_operating']), f"{row2['education_pct']:.1f}%",
                    f"{row2['health_pct']:.1f}%", f"{row2['economic_pct']:.1f}%"
                ]
            }
            
            compare_df = pd.DataFrame(compare_data)
            st.dataframe(compare_df, use_container_width=True, hide_index=True)
            
            # Visual comparison
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                # Execution rate comparison bar chart
                fig_exec_compare = go.Figure()
                fig_exec_compare.add_trace(go.Bar(
                    name=lgu1,
                    x=['Execution Rate'],
                    y=[row1['execution_rate']],
                    marker_color='#1f4e79'
                ))
                fig_exec_compare.add_trace(go.Bar(
                    name=lgu2,
                    x=['Execution Rate'],
                    y=[row2['execution_rate']],
                    marker_color='#4a90d9'
                ))
                fig_exec_compare.update_layout(
                    title='Execution Rate Comparison',
                    yaxis_title='Percentage (%)',
                    barmode='group',
                    showlegend=True
                )
                st.plotly_chart(fig_exec_compare, use_container_width=True)
            
            with col_viz2:
                # Sector spending comparison
                sectors = ['Education', 'Health', 'Economic']
                fig_sector = go.Figure()
                fig_sector.add_trace(go.Bar(
                    name=lgu1,
                    x=sectors,
                    y=[row1['education_pct'], row1['health_pct'], row1['economic_pct']],
                    marker_color='#1f4e79'
                ))
                fig_sector.add_trace(go.Bar(
                    name=lgu2,
                    x=sectors,
                    y=[row2['education_pct'], row2['health_pct'], row2['economic_pct']],
                    marker_color='#4a90d9'
                ))
                fig_sector.update_layout(
                    title='Sector Spending Comparison',
                    yaxis_title='Percentage of Expenditures (%)',
                    barmode='group',
                    showlegend=True
                )
                st.plotly_chart(fig_sector, use_container_width=True)
            
            # Insights comparison
            st.subheader("Key Insights Comparison")
            col_insight1, col_insight2 = st.columns(2)
            
            with col_insight1:
                st.markdown(f"**{lgu1}**")
                insights1 = get_insights(row1)
                if insights1:
                    for insight in insights1:
                        st.markdown(f"• {insight}")
                else:
                    st.markdown("*No significant flags*")
            
            with col_insight2:
                st.markdown(f"**{lgu2}**")
                insights2 = get_insights(row2)
                if insights2:
                    for insight in insights2:
                        st.markdown(f"• {insight}")
                else:
                    st.markdown("*No significant flags*")
            
            st.divider()
    
    # Summary statistics
    st.header("📈 Overview")
    stats = get_summary_stats(df_filtered)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total LGUs", f"{stats['total_lgus']}")
    
    with col2:
        avg_exec = stats['avg_execution']
        st.metric("Avg Execution", f"{avg_exec:.1f}%" if avg_exec else "N/A")
    
    with col3:
        st.metric("High Execution", f"{stats['high_execution']}", 
                 delta=f"{stats['high_execution']/stats['total_lgus']*100:.1f}%" if stats['total_lgus'] > 0 else "0%")
    
    with col4:
        st.metric("Low Execution", f"{stats['low_execution']}",
                 delta=f"{stats['low_execution']/stats['total_lgus']*100:.1f}%" if stats['total_lgus'] > 0 else "0%",
                 delta_color="inverse")
    
    with col5:
        avg_nta = stats['avg_nta_dependency']
        st.metric("Avg NTA Dependency", f"{avg_nta:.1f}%" if avg_nta else "N/A")
    
    # Charts
    st.header("📊 Analysis")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Execution rate distribution
        fig_exec = px.histogram(
            df_filtered, 
            x='execution_rate',
            nbins=20,
            title='Distribution of Execution Rates',
            labels={'execution_rate': 'Execution Rate (%)', 'count': 'Number of LGUs'},
            color='execution_category',
            color_discrete_map={
                'High': '#28a745',
                'Moderate': '#ffc107',
                'Low': '#dc3545'
            }
        )
        fig_exec.update_layout(showlegend=False)
        st.plotly_chart(fig_exec, use_container_width=True)
    
    with col_chart2:
        # NTA Dependency vs Execution Rate scatter
        fig_scatter = px.scatter(
            df_filtered,
            x='nta_dependency',
            y='execution_rate',
            color='execution_category',
            hover_data=['lgu_name', 'province'],
            title='NTA Dependency vs Execution Rate',
            labels={
                'nta_dependency': 'NTA Dependency (%)',
                'execution_rate': 'Execution Rate (%)'
            },
            color_discrete_map={
                'High': '#28a745',
                'Moderate': '#ffc107',
                'Low': '#dc3545'
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # LGU Scorecards
    st.header("🏛️ LGU Scorecards")
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ['Execution Rate (High to Low)', 'Execution Rate (Low to High)', 
         'NTA Dependency (High to Low)', 'Total Income (High to Low)']
    )
    
    if sort_by == 'Execution Rate (High to Low)':
        df_sorted = df_filtered.sort_values('execution_rate', ascending=False)
    elif sort_by == 'Execution Rate (Low to High)':
        df_sorted = df_filtered.sort_values('execution_rate', ascending=True)
    elif sort_by == 'NTA Dependency (High to Low)':
        df_sorted = df_filtered.sort_values('nta_dependency', ascending=False)
    else:
        df_sorted = df_filtered.sort_values('total_income', ascending=False)
    
    # Display scorecards
    for idx, row in df_sorted.head(20).iterrows():
        with st.container():
            col_main, col_metrics = st.columns([2, 3])
            
            with col_main:
                execution_color = get_execution_color(row['execution_category'])
                barmm_badge = "🟢 BARMM" if row['is_barmm'] else ""
                
                st.markdown(f"""
                <div class="scorecard">
                    <h3>{row['lgu_name']}, {row['province']} {barmm_badge}</h3>
                    <p style="color: #666; margin-top: -10px;">{row['lgu_type']} | {row['region']}</p>
                    <h2 style="color: {execution_color}; margin: 10px 0;">
                        {row['execution_rate']:.1f}% Execution
                    </h2>
                    <span style="background-color: {execution_color}; color: white; padding: 3px 10px; 
                                 border-radius: 12px; font-size: 0.8rem;">
                        {row['execution_category']}
                    </span>
                    <span style="background-color: {'#28a745' if row['fiscal_health'] == 'Surplus' else '#dc3545' if row['fiscal_health'] == 'Deficit' else '#6c757d'}; 
                                 color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; margin-left: 5px;">
                        {row['fiscal_health']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_metrics:
                m1, m2, m3, m4 = st.columns(4)
                
                with m1:
                    st.markdown(f"""
                    <div class="metric-label">{SPREADSHEET_COLUMNS['total_income']}</div>
                    <div class="metric-value">{format_currency(row['total_income'])}</div>
                    """, unsafe_allow_html=True)
                
                with m2:
                    st.markdown(f"""
                    <div class="metric-label">{SPREADSHEET_COLUMNS['total_expenditures']}</div>
                    <div class="metric-value">{format_currency(row['total_expenditures'])}</div>
                    """, unsafe_allow_html=True)
                
                with m3:
                    st.markdown(f"""
                    <div class="metric-label">National Tax Allotment (%)</div>
                    <div class="metric-value">{row['nta_dependency']:.1f}%</div>
                    """, unsafe_allow_html=True)
                
                with m4:
                    st.markdown(f"""
                    <div class="metric-label">{SPREADSHEET_COLUMNS['net_operating']}</div>
                    <div class="metric-value">{format_currency(row['net_operating'])}</div>
                    """, unsafe_allow_html=True)
                
                # Sector breakdown with exact spreadsheet headings
                st.markdown(f"**{SPREADSHEET_COLUMNS['total_social_services']} & {SPREADSHEET_COLUMNS['economic_services']}:**")
                sec1, sec2, sec3 = st.columns(3)
                
                with sec1:
                    st.markdown(f"📚 {SPREADSHEET_COLUMNS['education']}: **{row['education_pct']:.1f}%**")
                with sec2:
                    st.markdown(f"🏥 {SPREADSHEET_COLUMNS['health']}: **{row['health_pct']:.1f}%**")
                with sec3:
                    st.markdown(f"🏗️ {SPREADSHEET_COLUMNS['economic_services']}: **{row['economic_pct']:.1f}%**")
                
                # Insights
                insights = get_insights(row)
                if insights:
                    st.markdown("**Key Insights:**")
                    for insight in insights:
                        if 'Low' in insight or 'deficit' in insight.lower():
                            css_class = "insight-box insight-danger"
                        elif 'High' in insight or 'bottleneck' in insight.lower():
                            css_class = "insight-box insight-warning"
                        else:
                            css_class = "insight-box"
                        st.markdown(f'<div class="{css_class}">{insight}</div>', unsafe_allow_html=True)
            
            st.divider()
    
    # Data table
    st.header("📋 Full Data")
    
    display_cols = [
        'region', 'province', 'lgu_name', 'lgu_type', 
        'execution_rate', 'fiscal_health', 'nta_dependency',
        'education_pct', 'health_pct', 'economic_pct'
    ]
    
    st.dataframe(
        df_filtered[display_cols].round(2),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name='lgu_budget_scorecard.csv',
        mime='text/csv'
    )
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<small>Data Source: Bureau of Local Government Finance (BLGF) | "
        "Statement of Receipts and Expenditures FY 2024 | "
        "Built for UNDP Philippines Public Finance and Digital Governance Portfolio</small>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

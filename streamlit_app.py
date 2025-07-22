import streamlit as st
import asyncio
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import nest_asyncio
from typing import List, Dict, Any

from page_crawler_service import PageCrawlerService
from config import Config
from auth import is_authenticated, show_login_form, show_logout_option

# Enable nested asyncio loops for Streamlit
nest_asyncio.apply()

# Configure Streamlit page
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .success-card {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-card {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-card {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication first
if not is_authenticated():
    show_login_form()
    st.stop()

# Initialize session state (only if authenticated)
if 'service' not in st.session_state:
    st.session_state.service = PageCrawlerService()
if 'processing_results' not in st.session_state:
    st.session_state.processing_results = []
if 'current_progress' not in st.session_state:
    st.session_state.current_progress = 0
if 'current_status' not in st.session_state:
    st.session_state.current_status = ""

def update_progress(status: str, progress: int):
    """Update progress bar and status"""
    st.session_state.current_progress = progress
    st.session_state.current_status = status

def display_company_info(company_data: Dict[str, Any]):
    """Display extracted company information in a structured format"""
    
    if not company_data:
        st.error("No company data available to display")
        return
    
    # Display sector validation information if available
    if '_validation' in company_data:
        validation = company_data['_validation']
        if validation['corrections'] or validation['issues']:
            with st.expander("🔍 Sector Validation Results", expanded=False):
                if validation['corrections']:
                    st.success("✅ Applied Sector Corrections:")
                    for correction in validation['corrections']:
                        st.write(f"• {correction}")
                
                if validation['issues']:
                    st.warning("⚠️ Sector Validation Issues:")
                    for issue in validation['issues']:
                        st.write(f"• {issue}")
    
    # Company Information Section
    st.subheader("🏢 Company Information")
    company_info = company_data.get('company_info', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        if company_info.get('name'):
            st.markdown(f"**Company Name:** {company_info['name']}")
        if company_info.get('headline'):
            st.markdown(f"**Headline:** {company_info['headline']}")
        if company_info.get('description'):
            st.markdown(f"**Description:** {company_info['description']}")
        if company_info.get('company_type'):
            st.markdown(f"**Company Type:** {company_info['company_type']}")
        if company_info.get('industry'):
            st.markdown(f"**Industry:** {company_info['industry']}")
        if company_info.get('sub_industry'):
            st.markdown(f"**Sub-Industry:** {company_info['sub_industry']}")
        if company_info.get('solution_area'):
            st.markdown(f"**Solution Area:** {company_info['solution_area']}")
        if company_info.get('business_model'):
            st.markdown(f"**Business Model:** {company_info['business_model']}")
    
    with col2:
        if company_info.get('headquarter'):
            st.markdown(f"**Headquarters:** {company_info['headquarter']}")
        if company_info.get('city'):
            st.markdown(f"**City:** {company_info['city']}")
        if company_info.get('founded_year'):
            st.markdown(f"**Founded:** {company_info['founded_year']}")
        if company_info.get('employee_count'):
            st.markdown(f"**Employees:** {company_info['employee_count']}")
        if company_info.get('active_customers'):
            st.markdown(f"**Active Customers:** {company_info['active_customers']}")
        if company_info.get('available_countries'):
            st.markdown(f"**Available Countries:** {company_info['available_countries']}")
    
    # Services Section
    services = company_data.get('services', [])
    if services and any(service.get('name') for service in services):
        st.subheader("🛠️ Services")
        for i, service in enumerate(services):
            if service.get('name'):
                st.markdown(f"**{i+1}. {service['name']}**")
                if service.get('description'):
                    st.markdown(f"   - {service['description']}")
    
    # Products Section
    products = company_data.get('products', [])
    if products and any(product.get('name') for product in products):
        st.subheader("📦 Products")
        for i, product in enumerate(products):
            if product.get('name'):
                with st.expander(f"Product {i+1}: {product['name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if product.get('headline'):
                            st.markdown(f"**Headline:** {product['headline']}")
                        if product.get('description'):
                            st.markdown(f"**Description:** {product['description']}")
                        if product.get('value_proposition'):
                            st.markdown(f"**Value Proposition:** {product['value_proposition']}")
                        if product.get('business_model'):
                            st.markdown(f"**Business Model:** {product['business_model']}")
                        if product.get('industry'):
                            st.markdown(f"**Industry:** {product['industry']}")
                        if product.get('sub_industry'):
                            st.markdown(f"**Sub-Industry:** {product['sub_industry']}")
                        if product.get('solution_area'):
                            st.markdown(f"**Solution Area:** {product['solution_area']}")
                    
                    with col2:
                        if product.get('active_customers'):
                            st.markdown(f"**Active Customers:** {product['active_customers']}")
                        if product.get('integrations'):
                            st.markdown(f"**Integrations:** {product['integrations']}")
                        if product.get('partnerships'):
                            st.markdown(f"**Partnerships:** {product['partnerships']}")
                        if product.get('statistics_value'):
                            st.markdown(f"**Key Statistic:** {product['statistics_value']}")
                        if product.get('available_countries'):
                            st.markdown(f"**Available Countries:** {product['available_countries']}")

def display_crawling_summary(summary: Dict[str, Any]):
    """Display crawling summary with metrics"""
    
    if not summary:
        return
    
    st.subheader("📊 Crawling Summary")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pages", summary.get('total_pages', 0))
    with col2:
        st.metric("Pages with Content", summary.get('pages_with_content', 0))
    with col3:
        st.metric("Total Content Length", f"{summary.get('total_content_length', 0):,}")
    with col4:
        st.metric("Success Rate", f"{(summary.get('pages_with_content', 0) / max(summary.get('total_pages', 1), 1) * 100):.1f}%")
    
    # Pages details
    if summary.get('pages_crawled'):
        st.subheader("📄 Pages Crawled")
        pages_df = pd.DataFrame(summary['pages_crawled'])
        st.dataframe(pages_df, use_container_width=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🕷️ Genetic Page Crawler Service</h1>
        <p>Powered by Agno AI Agents - Extract comprehensive company information from websites</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Show logout option
    show_logout_option()
    
    # Validate configuration
    try:
        Config.validate_config()
        st.sidebar.success("✅ Configuration Valid")
    except ValueError as e:
        st.sidebar.error(f"❌ Configuration Error: {str(e)}")
        st.error("Please check your configuration settings. Make sure AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set in your environment variables.")
        st.stop()
    
    max_pages = st.sidebar.slider("Max Pages per Website", 1, 20, Config.MAX_PAGES_PER_DOMAIN)
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔍 Single Website", "📋 Batch Processing", "📊 Results & History", "🗄️ Database", "📥 Export", "⚙️ Agent Settings"])
    
    with tab1:
        st.header("Analyze Single Website")
        
        url_input = st.text_input(
            "Enter Company Website URL",
            placeholder="https://example.com",
            help="Enter the URL of the company website you want to analyze"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("🚀 Analyze Website", type="primary"):
                if url_input:
                    with st.spinner("Processing website..."):
                        # Progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def progress_callback(status, progress):
                            progress_bar.progress(progress)
                            status_text.text(status)
                        
                        # Process website
                        try:
                            result = asyncio.run(
                                st.session_state.service.process_company_website(
                                    url=url_input,
                                    max_pages=max_pages,
                                    progress_callback=progress_callback
                                )
                            )
                            
                            # Store result
                            st.session_state.processing_results.append(result)
                            
                            # Display results
                            if result['success']:
                                st.success(f"✅ Successfully analyzed {url_input}")
                                
                                # Display metrics
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Pages Crawled", result['pages_crawled'])
                                with col2:
                                    st.metric("Processing Time", f"{result['processing_time']}s")
                                with col3:
                                    company_name = result['company_data']['company_info']['name'] if result['company_data'] else "Unknown"
                                    st.metric("Company", company_name[:20] + "..." if len(company_name) > 20 else company_name)
                                
                                # Display company information
                                if result['company_data']:
                                    display_company_info(result['company_data'])
                                
                                # Display crawling summary
                                if result['crawling_summary']:
                                    display_crawling_summary(result['crawling_summary'])
                                    
                            else:
                                st.error(f"❌ Failed to analyze {url_input}")
                                st.error(f"Error: {result['error']}")
                                
                        except Exception as e:
                            st.error(f"❌ Unexpected error: {str(e)}")
                            
                else:
                    st.warning("Please enter a valid URL")
        
        with col2:
            if st.button("🧹 Clear Results"):
                st.session_state.processing_results.clear()
                st.session_state.service.clear_history()
                st.success("Results cleared")
    
    with tab2:
        st.header("Batch Processing")
        
        st.info("Process multiple websites at once. Enter one URL per line.")
        
        urls_text = st.text_area(
            "Enter Website URLs (one per line)",
            height=150,
            placeholder="https://example1.com\nhttps://example2.com\nhttps://example3.com"
        )
        
        if st.button("🚀 Process Batch", type="primary"):
            if urls_text.strip():
                urls = [url.strip() for url in urls_text.strip().split('\n') if url.strip()]
                
                if urls:
                    with st.spinner(f"Processing {len(urls)} websites..."):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def batch_progress_callback(status, progress):
                            progress_bar.progress(progress)
                            status_text.text(status)
                        
                        try:
                            results = asyncio.run(
                                st.session_state.service.batch_process_websites(
                                    urls=urls,
                                    max_pages_per_site=max_pages,
                                    progress_callback=batch_progress_callback
                                )
                            )
                            
                            # Store results
                            st.session_state.processing_results.extend(results)
                            
                            # Display summary
                            successful = sum(1 for r in results if r['success'])
                            failed = len(results) - successful
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Processed", len(results))
                            with col2:
                                st.metric("Successful", successful)
                            with col3:
                                st.metric("Failed", failed)
                            
                            if successful > 0:
                                st.success(f"✅ Successfully processed {successful} out of {len(results)} websites")
                            
                            if failed > 0:
                                st.warning(f"⚠️ {failed} websites failed to process")
                                
                        except Exception as e:
                            st.error(f"❌ Batch processing error: {str(e)}")
                else:
                    st.warning("No valid URLs found")
            else:
                st.warning("Please enter at least one URL")
    
    with tab3:
        st.header("Results & History")
        
        st.info("💡 **New!** All analyzed data is now automatically saved to database for persistent storage. Check the 'Database' tab for complete history!")
        
        st.subheader("📋 Current Session Results")
        
        if st.session_state.processing_results:
            st.subheader("📊 Processing Statistics")
            
            # Create summary statistics
            total_results = len(st.session_state.processing_results)
            successful_results = sum(1 for r in st.session_state.processing_results if r['success'])
            failed_results = total_results - successful_results
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Processed", total_results)
            with col2:
                st.metric("Successful", successful_results)
            with col3:
                st.metric("Failed", failed_results)
            with col4:
                success_rate = (successful_results / total_results * 100) if total_results > 0 else 0
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Results table
            st.subheader("📋 Processing History")
            
            # Prepare data for display
            display_data = []
            for result in st.session_state.processing_results:
                company_name = "Unknown"
                if result.get('company_data') and result['company_data'].get('company_info'):
                    company_name = result['company_data']['company_info'].get('name', 'Unknown')
                
                display_data.append({
                    'URL': result['url'],
                    'Company': company_name,
                    'Status': '✅ Success' if result['success'] else '❌ Failed',
                    'Pages Crawled': result['pages_crawled'],
                    'Processing Time (s)': result['processing_time'],
                    'Timestamp': result['timestamp']
                })
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
            
            # Show detailed results
            st.subheader("🔍 Detailed Results")
            
            # Select result to view
            selected_index = st.selectbox(
                "Select a result to view details:",
                range(len(st.session_state.processing_results)),
                format_func=lambda i: f"{st.session_state.processing_results[i]['url']} - {'✅' if st.session_state.processing_results[i]['success'] else '❌'}"
            )
            
            if selected_index is not None:
                selected_result = st.session_state.processing_results[selected_index]
                
                if selected_result['success']:
                    display_company_info(selected_result['company_data'])
                    if selected_result['crawling_summary']:
                        display_crawling_summary(selected_result['crawling_summary'])
                else:
                    st.error(f"Processing failed: {selected_result['error']}")
            
        else:
            st.info("No processing results available. Process some websites first!")
    
    with tab4:
        st.header("Database Management")
        
        # Database statistics
        try:
            stats = st.session_state.service.get_database_statistics()
            
            st.subheader("📊 Database Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Companies", stats['total_companies'])
            with col2:
                st.metric("Total Analyses", stats['total_results'])
            with col3:
                st.metric("Successful", stats['successful_results'])
            with col4:
                st.metric("Failed", stats['failed_results'])
            
            # Success rate chart
            if stats['total_results'] > 0:
                success_rate = (stats['successful_results'] / stats['total_results']) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Chart for success vs failure
                chart_data = pd.DataFrame({
                    'Status': ['Successful', 'Failed'],
                    'Count': [stats['successful_results'], stats['failed_results']]
                })
                
                if chart_data['Count'].sum() > 0:
                    fig = px.pie(chart_data, values='Count', names='Status', 
                               title="Analysis Success Rate")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Top industries
            if stats['top_industries']:
                st.subheader("🏭 Top Industries")
                industries_df = pd.DataFrame(stats['top_industries'])
                if not industries_df.empty:
                    fig = px.bar(industries_df, x='industry', y='count', 
                               title="Companies by Industry")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Recent activity
            if stats['recent_activity']:
                st.subheader("📈 Recent Activity (Last 30 Days)")
                activity_df = pd.DataFrame(stats['recent_activity'])
                if not activity_df.empty:
                    fig = px.line(activity_df, x='date', y='count', 
                                title="Daily Analysis Activity")
                    st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading database statistics: {str(e)}")
        
        st.markdown("---")
        
        # Company browser
        st.subheader("🏢 Company Database")
        
        # Search functionality
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("Search Companies", 
                                       placeholder="Search by name, industry, or description...")
        
        with col2:
            if st.button("🔍 Search", type="primary"):
                if search_query:
                    st.session_state.search_results = st.session_state.service.search_companies(search_query)
                else:
                    st.session_state.search_results = st.session_state.service.get_all_companies()
                
        # Show all companies by default
        if 'search_results' not in st.session_state:
            st.session_state.search_results = st.session_state.service.get_all_companies()
        
        # Display companies
        companies = st.session_state.search_results
        
        if companies:
            st.write(f"Found {len(companies)} companies")
            
            # Create a DataFrame for display
            display_companies = []
            for company in companies:
                # Safely handle None values
                name = company.get('name') or 'Unknown'
                url = company.get('url') or ''
                city = company.get('city') or ''
                headquarter = company.get('headquarter') or ''
                industry = company.get('industry') or 'N/A'
                sub_industry = company.get('sub_industry') or 'N/A'
                last_analyzed = company.get('last_analyzed')
                
                # Ensure all values are strings before slicing
                name = str(name) if name is not None else 'Unknown'
                url = str(url) if url is not None else ''
                city = str(city) if city is not None else ''
                headquarter = str(headquarter) if headquarter is not None else ''
                industry = str(industry) if industry is not None else 'N/A'
                sub_industry = str(sub_industry) if sub_industry is not None else 'N/A'
                
                display_companies.append({
                    'Name': name[:50] + ('...' if len(name) > 50 else ''),
                    'Industry': industry,
                    'Sub-Industry': sub_industry,
                    'Location': f"{city}, {headquarter}".strip(', '),
                    'Services': company.get('service_count', 0) or 0,
                    'Products': company.get('product_count', 0) or 0,
                    'Last Analyzed': str(last_analyzed)[:10] if last_analyzed else 'Never',
                    'URL': url[:50] + ('...' if len(url) > 50 else ''),
                    'ID': company.get('id', '')  # Hidden for selection
                })
            
            companies_df = pd.DataFrame(display_companies)
            
            # Display with selection
            selected_indices = st.multiselect(
                "Select companies to view details:",
                range(len(companies_df)),
                format_func=lambda i: f"{companies_df.iloc[i]['Name']} - {companies_df.iloc[i]['Industry']}"
            )
            
            # Show table
            st.dataframe(companies_df.drop('ID', axis=1), use_container_width=True)
            
            # Show detailed view for selected companies
            if selected_indices:
                st.subheader("📋 Company Details")
                
                for idx in selected_indices:
                    company_id = companies_df.iloc[idx]['ID']
                    company_details = st.session_state.service.get_company_details(company_id)
                    
                    if company_details:
                        with st.expander(f"🏢 {company_details.get('name', 'Unknown Company')}", expanded=True):
                            # Basic info
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**URL:** {company_details.get('url') or 'N/A'}")
                                st.markdown(f"**Industry:** {company_details.get('industry') or 'N/A'}")
                                st.markdown(f"**Sub-Industry:** {company_details.get('sub_industry') or 'N/A'}")
                                st.markdown(f"**Solution Area:** {company_details.get('solution_area') or 'N/A'}")
                                st.markdown(f"**Business Model:** {company_details.get('business_model') or 'N/A'}")
                            
                            with col2:
                                city = company_details.get('city') or ''
                                headquarter = company_details.get('headquarter') or ''
                                st.markdown(f"**Location:** {city}, {headquarter}")
                                st.markdown(f"**Founded:** {company_details.get('founded_year') or 'N/A'}")
                                st.markdown(f"**Employees:** {company_details.get('employee_count') or 'N/A'}")
                                st.markdown(f"**Customers:** {company_details.get('active_customers') or 'N/A'}")
                                st.markdown(f"**Countries:** {company_details.get('available_countries') or 'N/A'}")
                            
                            description = company_details.get('description')
                            if description:
                                st.markdown(f"**Description:** {description}")
                            
                            # Services
                            services = company_details.get('services') or []
                            if services:
                                st.markdown("**Services:**")
                                for service in services:
                                    service_name = service.get('name') or 'Unnamed Service'
                                    service_desc = service.get('description') or 'No description'
                                    st.markdown(f"• **{service_name}**: {service_desc}")
                            
                            # Products
                            products = company_details.get('products') or []
                            if products:
                                st.markdown("**Products:**")
                                for product in products:
                                    product_name = product.get('name') or 'Unnamed Product'
                                    product_desc = product.get('description') or 'No description'
                                    st.markdown(f"• **{product_name}**: {product_desc}")
                            
                            # Processing history
                            history = company_details.get('processing_history') or []
                            if history:
                                st.markdown(f"**Analysis History:** {len(history)} analyses")
                                with st.expander("View Analysis History"):
                                    for h in history[:5]:  # Show last 5
                                        status = "✅ Success" if h.get('success') else "❌ Failed"
                                        timestamp = h.get('timestamp') or 'Unknown'
                                        pages_crawled = h.get('pages_crawled') or 0
                                        st.markdown(f"• {timestamp} - {status} - {pages_crawled} pages")
                            
                            # Delete option
                            if st.button(f"🗑️ Delete {company_details.get('name', 'Company')}", key=f"delete_{company_id}"):
                                if st.session_state.service.delete_company(company_id):
                                    st.success("Company deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete company")
        else:
            st.info("No companies found in database. Process some websites first!")
        
        # Database export
        st.markdown("---")
        st.subheader("📤 Database Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export Database"):
                try:
                    data = st.session_state.service.export_database_data()
                    
                    # Convert to JSON for download
                    json_data = json.dumps(data, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label="💾 Download Database Export",
                        data=json_data,
                        file_name=f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    
                    companies_count = len(data.get('companies') or [])
                    st.success(f"Database export ready! Contains {companies_count} companies.")
                    
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        with col2:
            if st.button("🧹 Clear Session Results"):
                st.session_state.processing_results.clear()
                st.session_state.service.clear_history()
                st.success("Session results cleared (database preserved)")
    
    with tab5:
        st.header("Export Results")
        
        if st.session_state.processing_results:
            st.subheader("📥 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox("Export Format", ["JSON", "CSV"])
                
            with col2:
                filename = st.text_input("Filename (optional)", placeholder="results_export")
            
            if st.button("📥 Export Results", type="primary"):
                try:
                    if export_format == "JSON":
                        export_filename = st.session_state.service.export_results_to_json(
                            st.session_state.processing_results,
                            filename + ".json" if filename else None
                        )
                        st.success(f"✅ Results exported to {export_filename}")
                        
                        # Show download button
                        with open(export_filename, 'r', encoding='utf-8') as f:
                            json_data = f.read()
                        
                        st.download_button(
                            label="💾 Download JSON",
                            data=json_data,
                            file_name=export_filename,
                            mime="application/json"
                        )
                        
                    else:  # CSV
                        # Create CSV data
                        csv_data = []
                        for result in st.session_state.processing_results:
                            row = {
                                'url': result['url'],
                                'success': result['success'],
                                'pages_crawled': result['pages_crawled'],
                                'processing_time': result['processing_time'],
                                'timestamp': result['timestamp']
                            }
                            
                            if result.get('company_data') and result['company_data'].get('company_info'):
                                company_info = result['company_data']['company_info']
                                for key, value in company_info.items():
                                    row[f'company_{key}'] = value
                            
                            csv_data.append(row)
                        
                        df = pd.DataFrame(csv_data)
                        csv_string = df.to_csv(index=False)
                        
                        st.download_button(
                            label="💾 Download CSV",
                            data=csv_string,
                            file_name=filename + ".csv" if filename else "results_export.csv",
                            mime="text/csv"
                        )
                        
                        st.success("✅ CSV data prepared for download")
                        
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
            
            # Show raw JSON data
            if st.checkbox("Show Raw JSON Data"):
                st.json(st.session_state.processing_results)
                
        else:
            st.info("No results to export. Process some websites first!")
    
    with tab6:
        st.header("⚙️ Agent Settings")
        
        st.markdown("""
        <div class="info-card">
            <h4>🤖 AI Agent Configuration</h4>
            <p>Customize the extraction requirements for the AI agent that analyzes company websites.</p>
            <p>Changes will be applied immediately and will affect all future website analyses.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get current extraction requirements
        current_requirements = st.session_state.service.extractor_agent.get_extraction_requirements()
        
        # Create a text area for editing the requirements
        new_requirements = st.text_area(
            "Extraction Requirements",
            value=current_requirements,
            height=400,
            help="Edit the extraction requirements for the AI agent. These instructions guide what information is extracted from websites."
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                try:
                    # Update the extraction requirements
                    st.session_state.service.extractor_agent.update_extraction_requirements(new_requirements)
                    st.success("✅ Extraction requirements updated successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to update extraction requirements: {str(e)}")
        
        with col2:
            if st.button("🔄 Reset to Default"):
                try:
                    # Reset to default requirements
                    st.session_state.service.extractor_agent.reset_to_default_requirements()
                    st.experimental_rerun()  # Rerun the app to show updated requirements
                except Exception as e:
                    st.error(f"❌ Failed to reset extraction requirements: {str(e)}")
        
        # Information about the agent
        with st.expander("ℹ️ About the AI Agent"):
            st.markdown("""
            ### Company Extractor Agent
            
            This AI agent is powered by Azure OpenAI and is designed to extract structured company information from website content.
            
            The agent analyzes the text content crawled from company websites and extracts details such as:
            
            - Company information (name, description, industry, etc.)
            - Services offered
            - Products and their details
            - Business model and customer information
            
            ### Extraction Requirements
            
            The extraction requirements define what information the agent should look for and how it should structure the output.
            Modifying these requirements allows you to customize the extraction process to focus on specific types of information.
            
            ### Best Practices
            
            - Keep the structure consistent with the original format
            - Be specific about what information to extract
            - Include clear instructions for the AI agent
            - Test changes on a few websites before running batch processing
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>🕷️ Genetic Page Crawler Service | Powered by Agno AI Agents</p>
            <p>Built with Streamlit • Made with SAMET HAYMANA</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 
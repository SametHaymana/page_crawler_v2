"""
Database module for Genetic Page Crawler Service
SQLite database for persistent storage of analyzed company data
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
import os

class CrawlerDatabase:
    """SQLite database manager for crawler service"""
    
    def __init__(self, db_path: str = "crawler_database.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Companies table - main company information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    name TEXT,
                    headline TEXT,
                    description TEXT,
                    company_type TEXT,
                    industry TEXT,
                    sub_industry TEXT,
                    solution_area TEXT,
                    business_model TEXT,
                    headquarter TEXT,
                    city TEXT,
                    founded_year TEXT,
                    employee_count TEXT,
                    active_customers TEXT,
                    available_countries TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Processing results table - crawling statistics and metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_results (
                    id TEXT PRIMARY KEY,
                    company_id TEXT,
                    url TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    pages_crawled INTEGER,
                    processing_time REAL,
                    error_message TEXT,
                    crawling_summary TEXT, -- JSON
                    validation_info TEXT, -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """)
            
            # Services table - company services
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    name TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """)
            
            # Products table - company products
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    name TEXT,
                    headline TEXT,
                    description TEXT,
                    value_proposition TEXT,
                    business_model TEXT,
                    industry TEXT,
                    sub_industry TEXT,
                    solution_area TEXT,
                    active_customers TEXT,
                    integrations TEXT,
                    partnerships TEXT,
                    statistics_value TEXT,
                    available_countries TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_url ON companies (url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies (name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_results_url ON processing_results (url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_results_timestamp ON processing_results (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_company_id ON services (company_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_company_id ON products (company_id)")
            
            conn.commit()
    
    def save_processing_result(self, result: Dict[str, Any]) -> str:
        """Save a complete processing result to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            result_id = str(uuid.uuid4())
            company_id = None
            
            # Save company data if extraction was successful
            if result['success'] and result.get('company_data'):
                company_id = self._save_company_data(cursor, result['url'], result['company_data'])
            
            # Save processing result
            cursor.execute("""
                INSERT INTO processing_results 
                (id, company_id, url, success, pages_crawled, processing_time, error_message, 
                 crawling_summary, validation_info, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                company_id,
                result['url'],
                result['success'],
                result.get('pages_crawled', 0),
                result.get('processing_time', 0),
                result.get('error', None),
                json.dumps(result.get('crawling_summary', {})),
                json.dumps(result.get('company_data', {}).get('_validation', {})),
                result.get('timestamp', datetime.now().isoformat())
            ))
            
            conn.commit()
            return result_id
    
    def _save_company_data(self, cursor, url: str, company_data: Dict[str, Any]) -> str:
        """Save company data and return company ID"""
        company_info = company_data.get('company_info', {})
        company_id = str(uuid.uuid4())
        
        # Check if company already exists
        cursor.execute("SELECT id FROM companies WHERE url = ?", (url,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing company
            company_id = existing['id']
            cursor.execute("""
                UPDATE companies SET
                    name = ?, headline = ?, description = ?, company_type = ?,
                    industry = ?, sub_industry = ?, solution_area = ?, business_model = ?,
                    headquarter = ?, city = ?, founded_year = ?, employee_count = ?,
                    active_customers = ?, available_countries = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                company_info.get('name'),
                company_info.get('headline'),
                company_info.get('description'),
                company_info.get('company_type'),
                company_info.get('industry'),
                company_info.get('sub_industry'),
                company_info.get('solution_area'),
                company_info.get('business_model'),
                company_info.get('headquarter'),
                company_info.get('city'),
                company_info.get('founded_year'),
                company_info.get('employee_count'),
                company_info.get('active_customers'),
                company_info.get('available_countries'),
                company_id
            ))
            
            # Delete existing services and products to replace them
            cursor.execute("DELETE FROM services WHERE company_id = ?", (company_id,))
            cursor.execute("DELETE FROM products WHERE company_id = ?", (company_id,))
        else:
            # Insert new company
            cursor.execute("""
                INSERT INTO companies 
                (id, url, name, headline, description, company_type, industry, sub_industry,
                 solution_area, business_model, headquarter, city, founded_year, employee_count,
                 active_customers, available_countries)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id, url, company_info.get('name'), company_info.get('headline'),
                company_info.get('description'), company_info.get('company_type'),
                company_info.get('industry'), company_info.get('sub_industry'),
                company_info.get('solution_area'), company_info.get('business_model'),
                company_info.get('headquarter'), company_info.get('city'),
                company_info.get('founded_year'), company_info.get('employee_count'),
                company_info.get('active_customers'), company_info.get('available_countries')
            ))
        
        # Save services
        for service in company_data.get('services', []):
            if service.get('name'):
                cursor.execute("""
                    INSERT INTO services (id, company_id, name, description)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), company_id, service.get('name'), service.get('description')))
        
        # Save products
        for product in company_data.get('products', []):
            if product.get('name'):
                cursor.execute("""
                    INSERT INTO products 
                    (id, company_id, name, headline, description, value_proposition, business_model,
                     industry, sub_industry, solution_area, active_customers, integrations,
                     partnerships, statistics_value, available_countries)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), company_id, product.get('name'), product.get('headline'),
                    product.get('description'), product.get('value_proposition'), product.get('business_model'),
                    product.get('industry'), product.get('sub_industry'), product.get('solution_area'),
                    product.get('active_customers'), product.get('integrations'), product.get('partnerships'),
                    product.get('statistics_value'), product.get('available_countries')
                ))
        
        return company_id
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies with their basic info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, 
                       COALESCE(COUNT(DISTINCT s.id), 0) as service_count,
                       COALESCE(COUNT(DISTINCT p.id), 0) as product_count,
                       MAX(pr.timestamp) as last_analyzed
                FROM companies c
                LEFT JOIN services s ON c.id = s.company_id
                LEFT JOIN products p ON c.id = p.company_id
                LEFT JOIN processing_results pr ON c.id = pr.company_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """)
            
            companies = []
            for row in cursor.fetchall():
                company_dict = dict(row)
                # Ensure None values are handled properly
                if company_dict.get('service_count') is None:
                    company_dict['service_count'] = 0
                if company_dict.get('product_count') is None:
                    company_dict['product_count'] = 0
                companies.append(company_dict)
            
            return companies
    
    def get_company_details(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get complete company details including services and products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get company info
            cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
            company_row = cursor.fetchone()
            
            if not company_row:
                return None
            
            company = dict(company_row)
            
            # Get services
            cursor.execute("SELECT * FROM services WHERE company_id = ?", (company_id,))
            services = [dict(row) for row in cursor.fetchall()]
            
            # Get products
            cursor.execute("SELECT * FROM products WHERE company_id = ?", (company_id,))
            products = [dict(row) for row in cursor.fetchall()]
            
            # Get processing history
            cursor.execute("""
                SELECT * FROM processing_results 
                WHERE company_id = ? 
                ORDER BY timestamp DESC
            """, (company_id,))
            processing_history = [dict(row) for row in cursor.fetchall()]
            
            company['services'] = services
            company['products'] = products
            company['processing_history'] = processing_history
            
            return company
    
    def get_processing_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent processing results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pr.*, c.name as company_name
                FROM processing_results pr
                LEFT JOIN companies c ON pr.company_id = c.id
                ORDER BY pr.timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                result['crawling_summary'] = json.loads(result['crawling_summary'] or '{}')
                result['validation_info'] = json.loads(result['validation_info'] or '{}')
                results.append(result)
            
            return results
    
    def search_companies(self, query: str) -> List[Dict[str, Any]]:
        """Search companies by name, industry, or description"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_query = f"%{query.lower()}%"
            
            cursor.execute("""
                SELECT c.*, 
                       COALESCE(COUNT(DISTINCT s.id), 0) as service_count,
                       COALESCE(COUNT(DISTINCT p.id), 0) as product_count,
                       MAX(pr.timestamp) as last_analyzed
                FROM companies c
                LEFT JOIN services s ON c.id = s.company_id
                LEFT JOIN products p ON c.id = p.company_id
                LEFT JOIN processing_results pr ON c.id = pr.company_id
                WHERE LOWER(COALESCE(c.name, '')) LIKE ? 
                   OR LOWER(COALESCE(c.industry, '')) LIKE ?
                   OR LOWER(COALESCE(c.description, '')) LIKE ?
                   OR LOWER(COALESCE(c.headline, '')) LIKE ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """, (search_query, search_query, search_query, search_query))
            
            companies = []
            for row in cursor.fetchall():
                company_dict = dict(row)
                # Ensure None values are handled properly
                if company_dict.get('service_count') is None:
                    company_dict['service_count'] = 0
                if company_dict.get('product_count') is None:
                    company_dict['product_count'] = 0
                companies.append(company_dict)
            
            return companies
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total companies
            cursor.execute("SELECT COUNT(*) as count FROM companies")
            total_companies = cursor.fetchone()['count']
            
            # Total processing results
            cursor.execute("SELECT COUNT(*) as count FROM processing_results")
            total_results = cursor.fetchone()['count']
            
            # Successful vs failed
            cursor.execute("SELECT success, COUNT(*) as count FROM processing_results GROUP BY success")
            success_stats = {str(row['success']): row['count'] for row in cursor.fetchall()}
            
            # Top industries
            cursor.execute("""
                SELECT industry, COUNT(*) as count 
                FROM companies 
                WHERE industry IS NOT NULL 
                GROUP BY industry 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_industries = [dict(row) for row in cursor.fetchall()]
            
            # Recent activity
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM processing_results
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """)
            recent_activity = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_companies': total_companies,
                'total_results': total_results,
                'successful_results': success_stats.get('1', 0),
                'failed_results': success_stats.get('0', 0),
                'top_industries': top_industries,
                'recent_activity': recent_activity
            }
    
    def delete_company(self, company_id: str) -> bool:
        """Delete a company and all related data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete related data first (foreign key constraints)
            cursor.execute("DELETE FROM services WHERE company_id = ?", (company_id,))
            cursor.execute("DELETE FROM products WHERE company_id = ?", (company_id,))
            cursor.execute("DELETE FROM processing_results WHERE company_id = ?", (company_id,))
            cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data for backup purposes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Export all tables
            data = {}
            
            cursor.execute("SELECT * FROM companies")
            data['companies'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM processing_results")
            data['processing_results'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM services")
            data['services'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM products")
            data['products'] = [dict(row) for row in cursor.fetchall()]
            
            data['export_timestamp'] = datetime.now().isoformat()
            
            return data 
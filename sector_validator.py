import csv
import logging
from typing import List, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class SectorValidator:
    """Validator for industry, sub-industry, and solution area categories"""
    
    def __init__(self, csv_path: str = "sectors.csv"):
        self.csv_path = csv_path
        self.industries: Set[str] = set()
        self.sub_industries: Set[str] = set()
        self.solution_areas: Set[str] = set()
        self._load_sectors()
    
    def _load_sectors(self):
        """Load sectors from CSV file"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file, delimiter=';')
                
                # Skip header
                next(csv_reader)
                
                for row in csv_reader:
                    if len(row) >= 6:
                        # Industry (column 1)
                        if len(row) > 1 and row[1].strip():
                            self.industries.add(row[1].strip())
                        
                        # Sub-Industry (column 3)  
                        if len(row) > 3 and row[3].strip():
                            self.sub_industries.add(row[3].strip())
                        
                        # Solution Area (column 5)
                        if len(row) > 5 and row[5].strip():
                            self.solution_areas.add(row[5].strip())
            
            logger.info(f"Loaded {len(self.industries)} industries, {len(self.sub_industries)} sub-industries, {len(self.solution_areas)} solution areas")
            
        except FileNotFoundError:
            logger.error(f"Sectors CSV file not found: {self.csv_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading sectors: {str(e)}")
            raise
    
    def get_valid_industries(self) -> List[str]:
        """Get list of valid industries"""
        return sorted(list(self.industries))
    
    def get_valid_sub_industries(self) -> List[str]:
        """Get list of valid sub-industries"""
        return sorted(list(self.sub_industries))
    
    def get_valid_solution_areas(self) -> List[str]:
        """Get list of valid solution areas"""
        return sorted(list(self.solution_areas))
    
    def validate_industry(self, industry: str) -> bool:
        """Validate if industry is in allowed list"""
        if not industry:
            return True  # null values are allowed
        return industry.strip() in self.industries
    
    def validate_sub_industry(self, sub_industry: str) -> bool:
        """Validate if sub-industry is in allowed list"""
        if not sub_industry:
            return True  # null values are allowed
        return sub_industry.strip() in self.sub_industries
    
    def validate_solution_area(self, solution_area: str) -> bool:
        """Validate if solution area is in allowed list"""
        if not solution_area:
            return True  # null values are allowed
        return solution_area.strip() in self.solution_areas
    
    def find_closest_industry(self, text: str) -> str:
        """Find the closest matching industry from the text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Exact match first
        for industry in self.industries:
            if industry.lower() == text_lower:
                return industry
        
        # Partial match
        for industry in self.industries:
            if industry.lower() in text_lower or text_lower in industry.lower():
                return industry
        
        return None
    
    def find_closest_sub_industry(self, text: str) -> str:
        """Find the closest matching sub-industry from the text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Exact match first
        for sub_industry in self.sub_industries:
            if sub_industry.lower() == text_lower:
                return sub_industry
        
        # Partial match
        for sub_industry in self.sub_industries:
            if sub_industry.lower() in text_lower or text_lower in sub_industry.lower():
                return sub_industry
        
        return None
    
    def find_closest_solution_area(self, text: str) -> str:
        """Find the closest matching solution area from the text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Exact match first
        for solution_area in self.solution_areas:
            if solution_area.lower() == text_lower:
                return solution_area
        
        # Partial match
        for solution_area in self.solution_areas:
            if solution_area.lower() in text_lower or text_lower in solution_area.lower():
                return solution_area
        
        return None
    
    def get_sectors_summary(self) -> str:
        """Get a formatted summary of all valid sectors for the agent"""
        summary = f"""
VALID INDUSTRY CATEGORIES ({len(self.industries)} total):
{', '.join(self.get_valid_industries())}

VALID SUB-INDUSTRY CATEGORIES ({len(self.sub_industries)} total):
{', '.join(self.get_valid_sub_industries())}

VALID SOLUTION AREA CATEGORIES ({len(self.solution_areas)} total):
{', '.join(self.get_valid_solution_areas())}
"""
        return summary
    
    def validate_company_sectors(self, company_data: Dict) -> Dict:
        """Validate and potentially correct company sector data"""
        if not company_data:
            return company_data
        
        validation_results = {
            'valid': True,
            'corrections': [],
            'issues': []
        }
        
        # Validate company info
        if 'company_info' in company_data:
            company_info = company_data['company_info']
            
            # Industry validation
            if 'industry' in company_info and company_info['industry']:
                if not self.validate_industry(company_info['industry']):
                    closest = self.find_closest_industry(company_info['industry'])
                    if closest:
                        validation_results['corrections'].append(f"Industry '{company_info['industry']}' corrected to '{closest}'")
                        company_info['industry'] = closest
                    else:
                        validation_results['issues'].append(f"Industry '{company_info['industry']}' not found in valid categories")
                        validation_results['valid'] = False
            
            # Sub-industry validation
            if 'sub_industry' in company_info and company_info['sub_industry']:
                if not self.validate_sub_industry(company_info['sub_industry']):
                    closest = self.find_closest_sub_industry(company_info['sub_industry'])
                    if closest:
                        validation_results['corrections'].append(f"Sub-industry '{company_info['sub_industry']}' corrected to '{closest}'")
                        company_info['sub_industry'] = closest
                    else:
                        validation_results['issues'].append(f"Sub-industry '{company_info['sub_industry']}' not found in valid categories")
                        validation_results['valid'] = False
            
            # Solution area validation
            if 'solution_area' in company_info and company_info['solution_area']:
                if not self.validate_solution_area(company_info['solution_area']):
                    closest = self.find_closest_solution_area(company_info['solution_area'])
                    if closest:
                        validation_results['corrections'].append(f"Solution area '{company_info['solution_area']}' corrected to '{closest}'")
                        company_info['solution_area'] = closest
                    else:
                        validation_results['issues'].append(f"Solution area '{company_info['solution_area']}' not found in valid categories")
                        validation_results['valid'] = False
        
        # Validate products
        if 'products' in company_data:
            for i, product in enumerate(company_data['products']):
                # Product industry validation
                if 'industry' in product and product['industry']:
                    if not self.validate_industry(product['industry']):
                        closest = self.find_closest_industry(product['industry'])
                        if closest:
                            validation_results['corrections'].append(f"Product {i+1} industry '{product['industry']}' corrected to '{closest}'")
                            product['industry'] = closest
                        else:
                            validation_results['issues'].append(f"Product {i+1} industry '{product['industry']}' not found in valid categories")
                            validation_results['valid'] = False
                
                # Product sub-industry validation
                if 'sub_industry' in product and product['sub_industry']:
                    if not self.validate_sub_industry(product['sub_industry']):
                        closest = self.find_closest_sub_industry(product['sub_industry'])
                        if closest:
                            validation_results['corrections'].append(f"Product {i+1} sub-industry '{product['sub_industry']}' corrected to '{closest}'")
                            product['sub_industry'] = closest
                        else:
                            validation_results['issues'].append(f"Product {i+1} sub-industry '{product['sub_industry']}' not found in valid categories")
                            validation_results['valid'] = False
                
                # Product solution area validation
                if 'solution_area' in product and product['solution_area']:
                    if not self.validate_solution_area(product['solution_area']):
                        closest = self.find_closest_solution_area(product['solution_area'])
                        if closest:
                            validation_results['corrections'].append(f"Product {i+1} solution area '{product['solution_area']}' corrected to '{closest}'")
                            product['solution_area'] = closest
                        else:
                            validation_results['issues'].append(f"Product {i+1} solution area '{product['solution_area']}' not found in valid categories")
                            validation_results['valid'] = False
        
        company_data['_validation'] = validation_results
        return company_data 
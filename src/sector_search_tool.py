import json
from typing import List, Dict, Any
from sector_validator import SectorValidator

class SectorSearchTool:
    """Tool for searching and finding relevant sectors for company categorization"""
    
    def __init__(self):
        self.validator = SectorValidator()
    
    def search_industries(self, keywords: str, limit: int = 5) -> List[str]:
        """
        Search for relevant industries based on keywords
        
        Args:
            keywords: Keywords to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching industry names
        """
        if not keywords:
            return []
        
        keywords_lower = keywords.lower()
        matches = []
        
        for industry in self.validator.get_valid_industries():
            # Exact match gets highest priority
            if industry.lower() == keywords_lower:
                matches.insert(0, industry)
            # Partial match
            elif keywords_lower in industry.lower() or industry.lower() in keywords_lower:
                matches.append(industry)
        
        return matches[:limit]
    
    def search_sub_industries(self, keywords: str, limit: int = 10) -> List[str]:
        """
        Search for relevant sub-industries based on keywords
        
        Args:
            keywords: Keywords to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching sub-industry names
        """
        if not keywords:
            return []
        
        keywords_lower = keywords.lower()
        keywords_words = set(keywords_lower.split())
        matches = []
        
        for sub_industry in self.validator.get_valid_sub_industries():
            sub_industry_lower = sub_industry.lower()
            sub_industry_words = set(sub_industry_lower.split())
            
            # Exact match gets highest priority
            if sub_industry_lower == keywords_lower:
                matches.insert(0, sub_industry)
            # Check for word overlap
            elif keywords_lower in sub_industry_lower or sub_industry_lower in keywords_lower:
                matches.append(sub_industry)
            # Check for common words
            elif keywords_words.intersection(sub_industry_words):
                matches.append(sub_industry)
        
        return matches[:limit]
    
    def search_solution_areas(self, keywords: str, limit: int = 10) -> List[str]:
        """
        Search for relevant solution areas based on keywords
        
        Args:
            keywords: Keywords to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching solution area names
        """
        if not keywords:
            return []
        
        keywords_lower = keywords.lower()
        keywords_words = set(keywords_lower.split())
        matches = []
        
        for solution_area in self.validator.get_valid_solution_areas():
            solution_area_lower = solution_area.lower()
            solution_area_words = set(solution_area_lower.split())
            
            # Exact match gets highest priority
            if solution_area_lower == keywords_lower:
                matches.insert(0, solution_area)
            # Check for word overlap
            elif keywords_lower in solution_area_lower or solution_area_lower in keywords_lower:
                matches.append(solution_area)
            # Check for common words
            elif keywords_words.intersection(solution_area_words):
                matches.append(solution_area)
        
        return matches[:limit]
    
    def search_all_sectors(self, keywords: str) -> Dict[str, List[str]]:
        """
        Search across all sector types for the given keywords
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            Dictionary with industry, sub_industry, and solution_area results
        """
        return {
            "industries": self.search_industries(keywords, limit=3),
            "sub_industries": self.search_sub_industries(keywords, limit=5),
            "solution_areas": self.search_solution_areas(keywords, limit=5)
        }
    
    def get_sector_recommendations(self, company_description: str, technologies: List[str] = None) -> Dict[str, Any]:
        """
        Get sector recommendations based on company description and technologies
        
        Args:
            company_description: Description of the company
            technologies: List of technologies the company uses
            
        Returns:
            Dictionary with recommended sectors and reasoning
        """
        recommendations = {
            "recommended_industries": [],
            "recommended_sub_industries": [],
            "recommended_solution_areas": [],
            "reasoning": []
        }
        
        if not company_description:
            return recommendations
        
        # Extract key terms from description
        description_lower = company_description.lower()
        
        # Common technology/industry mappings
        tech_keywords = {
            "software": ["Information Technology", "Software Development"],
            "ai": ["Artificial Intelligence", "Machine Learning"],
            "blockchain": ["Blockchain", "Cryptocurrency"],
            "fintech": ["Finance", "Banking"],
            "healthcare": ["Healthcare", "Medical Services"],
            "ecommerce": ["E-Commerce", "Retail"],
            "logistics": ["Logistics", "Transportation"],
            "marketing": ["Marketing", "Digital Marketing"],
            "education": ["Education", "E-Learning"],
            "gaming": ["Gaming", "Entertainment"]
        }
        
        # Search for relevant sectors based on description
        for keyword, related_sectors in tech_keywords.items():
            if keyword in description_lower:
                for sector in related_sectors:
                    # Search for this sector in our valid categories
                    industry_matches = self.search_industries(sector)
                    sub_industry_matches = self.search_sub_industries(sector)
                    solution_area_matches = self.search_solution_areas(sector)
                    
                    if industry_matches:
                        recommendations["recommended_industries"].extend(industry_matches[:2])
                        recommendations["reasoning"].append(f"Found '{keyword}' in description, suggesting {industry_matches[0]} industry")
                    
                    if sub_industry_matches:
                        recommendations["recommended_sub_industries"].extend(sub_industry_matches[:3])
                    
                    if solution_area_matches:
                        recommendations["recommended_solution_areas"].extend(solution_area_matches[:3])
        
        # Add technology-specific recommendations
        if technologies:
            for tech in technologies:
                tech_results = self.search_all_sectors(tech)
                recommendations["recommended_solution_areas"].extend(tech_results["solution_areas"][:2])
                recommendations["reasoning"].append(f"Technology '{tech}' suggests solution areas: {', '.join(tech_results['solution_areas'][:2])}")
        
        # Remove duplicates while preserving order
        recommendations["recommended_industries"] = list(dict.fromkeys(recommendations["recommended_industries"]))
        recommendations["recommended_sub_industries"] = list(dict.fromkeys(recommendations["recommended_sub_industries"]))
        recommendations["recommended_solution_areas"] = list(dict.fromkeys(recommendations["recommended_solution_areas"]))
        
        return recommendations

# Tool functions for the agent
def search_sectors_by_keywords(keywords: str) -> str:
    """
    Tool function to search for sectors by keywords
    Available to the agent for sector lookup
    """
    tool = SectorSearchTool()
    results = tool.search_all_sectors(keywords)
    return json.dumps(results, indent=2)

def get_sector_recommendations_for_company(company_description: str, technologies: str = "") -> str:
    """
    Tool function to get sector recommendations for a company
    Available to the agent for intelligent sector suggestions
    """
    tool = SectorSearchTool()
    tech_list = [t.strip() for t in technologies.split(",") if t.strip()] if technologies else []
    recommendations = tool.get_sector_recommendations(company_description, tech_list)
    return json.dumps(recommendations, indent=2) 
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.azure import AzureOpenAI
from typing import Dict, Any, Optional
import json
from textwrap import dedent
from config import Config
from sector_validator import SectorValidator
from sector_search_tool import search_sectors_by_keywords, get_sector_recommendations_for_company
import logging

logger = logging.getLogger(__name__)

class CompanyExtractorAgent:
    """Agno AI Agent for extracting structured company information from website content"""
    
    def __init__(self):
        self.sector_validator = SectorValidator()
        self._default_extraction_requirements = """
        Extract comprehensive company information organized into three main sections:

        1. COMPANY INFORMATION:
        - Company Logo: Look for company logo in website header or media kit
        - Company Name: Complete, official company name without abbreviations
        - Headline/Tagline: Short value statement used prominently on website
        - Description: Company mission, core activities, target market in detail
        - Company Type: Legal/organizational type (Technology Company, Corporate, etc.)
        - Service or Product: Whether company is product-based, service-based, or both
        - Company Video URL: YouTube link to company introduction video
        - Headquarter: Country where company headquarters is located
        - City: Name of city where main office is located
        - Employee Count: Most recent estimate of full-time employees
        - Founded Year: Year the company was established
        - Business Model: B2B, B2C, B2B2C, C2C, etc.
        - Women Founded: Whether any founders are women
        - Industry: Core industries the company serves (MUST use sector search tools)
        - Sub-Industry: Niche areas within main industries (MUST use sector search tools)
        - Solution Area: Technology-driven focus areas (MUST use sector search tools)
        - Tags: Relevant hashtags highlighting company focus
        - Active Customers: Well-known brands using company offerings
        - Available Countries: Countries where company has presence

        CRITICAL SECTOR SELECTION PROCESS:
        For Industry, Sub-Industry, and Solution Area fields, you MUST:
        1. First use the 'get_sector_recommendations_for_company' tool with the company description
        2. If no good recommendations, use 'search_sectors_by_keywords' tool with relevant terms
        3. Only select from the results returned by these tools
        4. DO NOT create new categories or guess - only use what the tools return

        2. SERVICES INFORMATION:
        For each service offered:
        - Service Name: Official or recognized name/marketing title
        - Service Description: What service does and value it provides

        3. PRODUCTS INFORMATION:
        For each product offered:
        - Product Logo, Name, Headline, Description
        - Product Video, Founded Year, Business Model
        - Industry, Sub-Industry, Solution Area (MUST use sector search tools)
        - Screenshots, How Product Works (5 steps max)
        - Value Proposition (240 chars max)
        - Use Case Title & Description (240 chars)
        - Case Study Title, Customer Name, Description
        - Statistics Title & Value
        - Active Customers, Customer Logos
        - Available Countries, Integrations, Partnerships
        """
        
        self._extraction_requirements = self._default_extraction_requirements
        self.agent = self._create_agent()
    
    def get_extraction_requirements(self) -> str:
        """Get the current extraction requirements"""
        return self._extraction_requirements
    
    def update_extraction_requirements(self, new_requirements: str) -> None:
        """
        Update the extraction requirements and recreate the agent
        
        Args:
            new_requirements: New extraction requirements text
        """
        if not new_requirements or not new_requirements.strip():
            logger.warning("Empty requirements provided, using default requirements")
            self._extraction_requirements = self._default_extraction_requirements
        else:
            logger.info("Updating extraction requirements")
            self._extraction_requirements = new_requirements
        
        # Recreate the agent with the updated requirements
        self.agent = self._create_agent()
        logger.info("Agent recreated with updated extraction requirements")
    
    def reset_to_default_requirements(self) -> None:
        """Reset extraction requirements to default and recreate the agent"""
        logger.info("Resetting extraction requirements to default")
        self._extraction_requirements = self._default_extraction_requirements
        self.agent = self._create_agent()
        logger.info("Agent reset to default extraction requirements")
    
    def _create_agent(self) -> Agent:
        """Create and configure the Agno agent for company data extraction"""
        
        agent = Agent(
            model=AzureOpenAI(
                id=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_key=Config.AZURE_OPENAI_API_KEY,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
                api_version=Config.AZURE_OPENAI_API_VERSION
            ),
            tools=[search_sectors_by_keywords, get_sector_recommendations_for_company],
            description=dedent("""\
                You are an expert Company Information Extraction Specialist, an AI agent designed 
                to analyze website content and extract comprehensive company information with 
                precision and thoroughness.

                Your expertise includes:
                - Company profile analysis and data extraction
                - Product and service identification and categorization  
                - Business intelligence gathering from web content
                - Structured data organization and validation
                - Multi-language content processing (English and Turkish)
                
                You excel at finding subtle details, cross-referencing information across 
                multiple pages, and organizing complex company data into structured formats.
            """),
            
            instructions=dedent(f"""\
                You will receive website content that has been crawled from a company's website.
                Your task is to analyze this content thoroughly and extract structured information
                following these detailed requirements:

                {self._extraction_requirements}

                IMPORTANT ANALYSIS GUIDELINES:
                1. READ ALL provided website content carefully - content from multiple pages will be provided
                2. Cross-reference information across different pages to ensure accuracy
                3. Look for patterns and consistent information across the website
                4. Prioritize official company statements over informal content
                5. Extract exact text/names when possible rather than paraphrasing
                6. If multiple variations of the same information exist, choose the most official/recent version
                7. Pay special attention to About Us, Products, Services, and Contact pages
                8. Look for company logos, videos, and visual content references in the text
                9. Extract customer names, case studies, and testimonials when available
                10. Identify integration partners and technology stacks mentioned

                SECTOR CATEGORIZATION PROCESS:
                For Industry, Sub-Industry, and Solution Area fields, you MUST use the provided tools:
                
                1. FIRST: Use 'get_sector_recommendations_for_company' with the company description
                   - This will give you intelligent recommendations based on the company's description
                   
                2. SECOND: If you need more options, use 'search_sectors_by_keywords' with relevant terms
                   - Search using keywords like: "fintech", "healthcare", "AI", "software", etc.
                   
                3. ONLY select from the sectors returned by these tools
                4. DO NOT make up sector names or use sectors not returned by the tools

                CRITICAL OUTPUT REQUIREMENTS:
                - Your response MUST be valid JSON only
                - No additional text, explanations, or comments outside the JSON
                - Use null for any information that cannot be found
                - Ensure all strings are properly escaped for JSON format
                - Double-check that all JSON brackets and syntax are correct
                
                Remember: The quality of extraction depends on thorough analysis of ALL provided content.
                Be meticulous and comprehensive in your analysis.
            """),
            
            expected_output=dedent("""\
                A valid JSON object with exactly this structure:
                {
                    "company_info": {
                        "logo": "string or null",
                        "name": "string or null", 
                        "headline": "string or null",
                        "description": "string or null",
                        "company_type": "string or null",
                        "service_or_product": "string or null",
                        "video_url": "string or null",
                        "headquarter": "string or null",
                        "city": "string or null",
                        "employee_count": "string or null",
                        "founded_year": "string or null",
                        "business_model": "string or null",
                        "women_founded": "string or null",
                        "industry": "string or null",
                        "sub_industry": "string or null",
                        "solution_area": "string or null",
                        "tags": "string or null",
                        "active_customers": "string or null",
                        "available_countries": "string or null"
                    },
                    "services": [
                        {
                            "name": "string or null",
                            "description": "string or null"
                        }
                    ],
                    "products": [
                        {
                            "logo": "string or null",
                            "name": "string or null",
                            "headline": "string or null",
                            "description": "string or null",
                            "video": "string or null",
                            "employee_count": "string or null",
                            "founded_year": "string or null",
                            "business_model": "string or null",
                            "industry": "string or null",
                            "sub_industry": "string or null",
                            "solution_area": "string or null",
                            "screenshots": "string or null",
                            "how_it_works": "string or null",
                            "value_proposition": "string or null",
                            "use_case_title": "string or null",
                            "use_case_description": "string or null",
                            "case_study_title": "string or null",
                            "customer_name": "string or null",
                            "case_study_description": "string or null",
                            "statistics_title": "string or null",
                            "statistics_value": "string or null",
                            "active_customers": "string or null",
                            "customer_logos": "string or null",
                            "available_countries": "string or null",
                            "integrations": "string or null",
                            "partnerships": "string or null"
                        }
                    ]
                }
            """),
            
            markdown=False,
            show_tool_calls=True,
            add_datetime_to_instructions=False
        )
        
        return agent
    
    def extract_company_info(self, website_content: str) -> Optional[Dict[Any, Any]]:
        """
        Extract company information from website content using the Agno agent
        
        Args:
            website_content: Combined text content from crawled website pages
            
        Returns:
            Dictionary containing structured company information or None if extraction fails
        """
        try:
            logger.info("Starting company information extraction...")
            
            # Prepare the prompt with website content
            extraction_prompt = f"""
            Please analyze the following website content and extract comprehensive company information.
            
            WEBSITE CONTENT TO ANALYZE:
            {website_content}
            
            Extract all available information following the detailed requirements provided in the instructions.
            Return only valid JSON format with no additional text.
            """
            
            # Get response from agent
            response = self.agent.run(extraction_prompt)
            
            # Parse the JSON response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Clean the response text (remove any markdown formatting)
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                company_data = json.loads(response_text)
                
                # Apply sector validation and corrections
                validated_data = self.sector_validator.validate_company_sectors(company_data)
                
                # Log validation results
                if '_validation' in validated_data:
                    validation = validated_data['_validation']
                    if validation['corrections']:
                        logger.info(f"Applied sector corrections: {validation['corrections']}")
                    if validation['issues']:
                        logger.warning(f"Sector validation issues: {validation['issues']}")
                    if not validation['valid']:
                        logger.error("Critical sector validation failed")
                
                logger.info("Successfully extracted and validated company information")
                return validated_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response text: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"Error during company information extraction: {str(e)}")
            return None
    
    def validate_extraction_result(self, result: Dict[Any, Any]) -> bool:
        """
        Validate that the extraction result has the expected structure
        
        Args:
            result: The extracted company information dictionary
            
        Returns:
            True if the structure is valid, False otherwise
        """
        try:
            # Check main sections exist
            required_sections = ['company_info', 'services', 'products']
            for section in required_sections:
                if section not in result:
                    logger.error(f"Missing required section: {section}")
                    return False
            
            # Check company_info has required structure
            if not isinstance(result['company_info'], dict):
                logger.error("company_info is not a dictionary")
                return False
            
            # Check services is a list
            if not isinstance(result['services'], list):
                logger.error("services is not a list")
                return False
            
            # Check products is a list  
            if not isinstance(result['products'], list):
                logger.error("products is not a list")
                return False
            
            logger.info("Extraction result validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False 
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.azure import AzureOpenAI
from typing import Dict, Any, Optional, List
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
    
    @classmethod
    def create_agent_pool(cls, pool_size: int) -> List['CompanyExtractorAgent']:
        """
        Create a pool of CompanyExtractorAgent instances for parallel processing
        
        Args:
            pool_size: Number of agent instances to create
            
        Returns:
            List of CompanyExtractorAgent instances
        """
        logger.info(f"Creating a pool of {pool_size} CompanyExtractorAgent instances")
        return [cls() for _ in range(pool_size)]
    
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
                - Your response MUST be valid JSON only - no additional text, explanations, or comments
                - Use null for any information that cannot be found
                - Ensure all strings are properly escaped for JSON format
                - Double-check that all JSON brackets and syntax are correct
                - Do not include any HTML tags, script tags, or special characters in the JSON
                - Keep all string values simple and clean - avoid complex formatting
                - If a field contains multiple values, separate them with commas in a single string
                - Never use backticks, angle brackets, or other special characters in string values
                
                JSON STRUCTURE VALIDATION:
                - All property names must be in double quotes
                - All string values must be in double quotes
                - Use null (without quotes) for missing values
                - Ensure proper nesting of objects and arrays
                - No trailing commas after the last item in objects or arrays
                
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
            
            # Parse JSON with improved error handling
            try:
                # First, try to clean the response text more thoroughly
                cleaned_text = self._clean_json_response(response_text)
                
                # Try to parse the cleaned JSON
                company_data = json.loads(cleaned_text)
                
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
                logger.error(f"Original response text: {response_text}")
                
                # Try to fix common JSON issues
                try:
                    fixed_text = self._fix_json_syntax(response_text)
                    company_data = json.loads(fixed_text)
                    
                    # Apply sector validation and corrections
                    validated_data = self.sector_validator.validate_company_sectors(company_data)
                    
                    logger.info("Successfully extracted company information after JSON fixes")
                    return validated_data
                    
                except (json.JSONDecodeError, Exception) as fix_error:
                    logger.error(f"Failed to fix JSON syntax: {fix_error}")
                    logger.error(f"Attempted fix: {fixed_text}")
                    
                    # Create a fallback structure with basic information
                    logger.warning("Creating fallback company data structure due to JSON parsing failure")
                    fallback_data = self._create_fallback_structure()
                    return fallback_data
                
        except Exception as e:
            logger.error(f"Error during company information extraction: {str(e)}")
            return None
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean the JSON response text to remove common formatting issues"""
        # Remove markdown code blocks
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Remove any leading/trailing whitespace
        response_text = response_text.strip()
        
        # Remove any explanatory text before or after JSON
        lines = response_text.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('{') or line.startswith('['):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.endswith('}') or line.endswith(']'):
                in_json = False
        
        return '\n'.join(json_lines)
    
    def _fix_json_syntax(self, json_text: str) -> str:
        """Attempt to fix common JSON syntax errors"""
        import re
        
        # Fix common issues
        fixed_text = json_text
        
        # Remove any script tags or HTML that might have been included
        fixed_text = re.sub(r'<script[^>]*>.*?</script>', '', fixed_text, flags=re.DOTALL)
        fixed_text = re.sub(r'<[^>]*>', '', fixed_text)
        
        # Fix malformed field names with spaces or special characters
        fixed_text = re.sub(r'"([^"]*)\s+([^"]*)"\s*:', r'"\1_\2":', fixed_text)
        
        # Fix missing quotes around property names
        fixed_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_text)
        
        # Fix trailing commas
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        # Fix null values that might be malformed
        fixed_text = re.sub(r':\s*null\s*([,}])', r': null\1', fixed_text)
        
        # Fix string values that might be malformed
        fixed_text = re.sub(r':\s*"([^"]*)"\s*([,}])', r': "\1"\2', fixed_text)
        
        # Fix any remaining malformed characters
        fixed_text = re.sub(r'[^\x20-\x7E\n\r\t]', '', fixed_text)
        
        # Fix specific issues from the error we saw
        fixed_text = re.sub(r'`([^`]*)`', r'"\1"', fixed_text)  # Replace backticks with quotes
        fixed_text = re.sub(r'\[\[([^\]]*)\]\]', r'"\1"', fixed_text)  # Replace double brackets
        fixed_text = re.sub(r'PARTNERS\s*/\*([^*]*)\*/', r'"\1"', fixed_text)  # Fix comment-like structures
        
        return fixed_text
    
    def _create_fallback_structure(self) -> Dict[str, Any]:
        """Create a fallback company data structure when JSON parsing fails"""
        return {
            "company_info": {
                "logo": None,
                "name": "Unknown Company",
                "headline": None,
                "description": "Company information extraction failed due to technical issues.",
                "company_type": None,
                "service_or_product": None,
                "video_url": None,
                "headquarter": None,
                "city": None,
                "employee_count": None,
                "founded_year": None,
                "business_model": None,
                "women_founded": None,
                "industry": None,
                "sub_industry": None,
                "solution_area": None,
                "tags": None,
                "active_customers": None,
                "available_countries": None
            },
            "services": [],
            "products": []
        }
    
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
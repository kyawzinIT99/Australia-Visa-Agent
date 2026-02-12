import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class SearchService:
    """Service for real-time web search using Tavily API."""
    
    def __init__(self):
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        self.client = TavilyClient(api_key=api_key)
        self.cache = {}  # Simple in-memory cache
    
    def search_australia_visa(self, query, max_results=3):
        """
        Search for Australia visa information with focus on official sources.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            dict with 'results' and 'answer' keys
        """
        # Check cache first
        cache_key = f"{query}_{max_results}"
        if cache_key in self.cache:
            print(f"[CACHE HIT] Returning cached results for: {query}")
            return self.cache[cache_key]
        
        try:
            # Search with focus on Australian government sources
            enhanced_query = f"Australian Department of Home Affairs {query} official requirements"
            
            response = self.client.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=["homeaffairs.gov.au", "immi.homeaffairs.gov.au", "australia.gov.au"],
                include_answer=True
            )
            
            # Cache the result
            self.cache[cache_key] = response
            
            print(f"[SEARCH] Found {len(response.get('results', []))} results for: {query}")
            return response
            
        except Exception as e:
            print(f"[ERROR] Tavily search failed: {e}")
            return {
                'results': [],
                'answer': None,
                'error': str(e)
            }
    
    def get_visa_requirements(self, visa_subclass):
        """Get specific requirements for a visa subclass."""
        query = f"visa subclass {visa_subclass} requirements documents checklist"
        return self.search_australia_visa(query)
    
    def get_document_guidance(self, document_type, visa_subclass):
        """Get guidance on completing a specific document type."""
        query = f"{document_type} requirements for visa subclass {visa_subclass}"
        return self.search_australia_visa(query)
    
    def verify_information(self, claim):
        """Verify a specific claim about Australian visa requirements."""
        query = f"verify: {claim}"
        return self.search_australia_visa(query, max_results=2)

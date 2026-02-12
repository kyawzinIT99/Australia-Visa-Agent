import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from services.search_service import SearchService

load_dotenv()

class AssistantService:
    """AI Assistant for helping applicants complete visa documents."""
    
    SYSTEM_PROMPT = """You are a professional Australia Visa Assistant helping applicants complete their visa documents.

CORE RULES:
1. ALWAYS search for current Australia visa requirements before answering visa-specific questions
2. Be friendly, patient, and encouraging
3. Provide step-by-step guidance
4. Cite official sources (Australian Department of Home Affairs)
5. If unsure, search rather than guess
6. Never hallucinate visa requirements - only provide information from search results

TONE:
- Professional yet warm
- Patient and understanding
- Clear and concise
- Encouraging and supportive

CAPABILITIES:
- Explain visa subclass requirements
- Guide document completion
- Clarify missing information
- Provide official sources
- Answer questions about Australian visa process

When answering visa-related questions:
1. First, search for the latest information
2. Cite the sources you found
3. Provide clear, actionable guidance
4. Offer to help with next steps

Remember: You're here to help applicants succeed. Be their trusted guide through the visa process."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.search_service = SearchService()
        self.conversation_history = []
        self.agent_config = self._load_agent_config()
        self.system_prompt = self._build_system_prompt()

    def _load_agent_config(self):
        """Load agent contact configuration."""
        try:
            config_path = os.path.join(os.getcwd(), 'agent_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading agent config: {e}")
        return {}

    def _build_system_prompt(self):
        """Build the system prompt with dynamic contact info."""
        config = self.agent_config
        contact_info = f"""
AGENT CONTACT DETAILS:
Name: {config.get('agent_name', 'Australia Visa Specialist')}
Email: {config.get('email', 'N/A')}
Phone: {config.get('phone', 'N/A')}
Address: {config.get('address', 'N/A')}
Website: {config.get('website', 'N/A')}
"""

        return f"""You are a professional Australia Visa Assistant helping applicants complete their visa documents.

CORE RULES:
1. STRICTLY answer ONLY questions related to Australian visas, immigration, and document preparation.
2. REFUSE to answer general knowledge questions (e.g., "What is the capital of France?", "Write a poem", "Python code"). Politely state: "I can only assist with Australian visa and immigration matters."
3. ALWAYS search for current Australia visa requirements before answering visa-specific questions.
4. Be friendly, patient, and encouraging.
5. Provide step-by-step guidance.
6. Cite official sources (Australian Department of Home Affairs).
7. If unsure, search rather than guess.
8. Never hallucinate visa requirements.

{contact_info}

INSTRUCTIONS FOR CONTACT INFO:
- If a user asks for contact information, support, or how to reach the agent, provide the details listed above.
- Do not invent contact details. Use ONLY what is provided.

TONE:
- Professional yet warm
- Patient and understanding
- Clear and concise
- Encouraging and supportive

CAPABILITIES:
- Explain visa subclass requirements
- Guide document completion
- Clarify missing information
- Provide official sources
- Answer questions about Australian visa process

When answering visa-related questions:
1. First, search for the latest information
2. Cite the sources you found
3. Provide clear, actionable guidance
4. Offer to help with next steps

Remember: You're here to help applicants succeed. Be their trusted guide through the visa process."""
    
    def chat(self, user_message, context=None):
        """
        Process user message and return AI response with search-grounded information.
        
        Args:
            user_message: User's question or request
            context: Optional context (e.g., current document being reviewed)
            
        Returns:
            dict with 'response', 'sources', and 'searched' keys
        """
        # Determine if we need to search
        needs_search = self._needs_search(user_message)
        search_results = None
        sources = []
        
        if needs_search:
            # Extract search query from user message
            search_query = self._extract_search_query(user_message)
            search_results = self.search_service.search_australia_visa(search_query)
            
            # Extract sources
            if search_results.get('results'):
                sources = [
                    {
                        'title': r.get('title', 'Unknown'),
                        'url': r.get('url', ''),
                        'snippet': r.get('content', '')[:200] + '...'
                    }
                    for r in search_results['results'][:3]
                ]
        
        # Build messages for OpenAI
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history (last 5 messages)
        messages.extend(self.conversation_history[-10:])
        
        # Add context if provided
        if context:
            context_msg = f"\n\nCONTEXT: {json.dumps(context)}"
            user_message += context_msg
        
        # Add search results if available
        if search_results and search_results.get('results'):
            search_context = "\n\nSEARCH RESULTS FROM OFFICIAL SOURCES:\n"
            for i, result in enumerate(search_results['results'][:3], 1):
                search_context += f"\n{i}. {result.get('title', 'Unknown')}\n"
                search_context += f"   Source: {result.get('url', 'N/A')}\n"
                search_context += f"   {result.get('content', '')[:300]}...\n"
            
            if search_results.get('answer'):
                search_context += f"\n\nSUMMARY: {search_results['answer']}\n"
            
            user_message += search_context
        
        messages.append({"role": "user", "content": user_message})
        
        # Get AI response
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            assistant_message = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return {
                'response': assistant_message,
                'sources': sources,
                'searched': needs_search
            }
            
        except Exception as e:
            print(f"[ERROR] OpenAI API failed: {e}")
            return {
                'response': "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                'sources': [],
                'searched': False,
                'error': str(e)
            }
    
    def _needs_search(self, message):
        """Determine if message requires searching for information."""
        search_keywords = [
            'requirement', 'document', 'visa', 'subclass', 'need', 'how to',
            'what is', 'explain', 'guide', 'help', 'complete', 'fill',
            'australia', 'immigration', 'application'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in search_keywords)
    
    def _extract_search_query(self, message):
        """Extract a search query from user message."""
        # Simple extraction - could be improved with NLP
        return message
    
    def get_document_help(self, document_type, visa_subclass, current_analysis=None):
        """Get specific help for completing a document."""
        context = {
            'document_type': document_type,
            'visa_subclass': visa_subclass,
            'current_analysis': current_analysis
        }
        
        prompt = f"I need help completing my {document_type} for visa subclass {visa_subclass}. "
        if current_analysis:
            prompt += f"The AI analysis shows a completeness score of {current_analysis.get('completeness_score', 0)}%. "
            if current_analysis.get('missing_items'):
                prompt += f"Missing items: {', '.join(current_analysis['missing_items'])}. "
        
        prompt += "What do I need to do?"
        
        return self.chat(prompt, context=context)
    
    def generate_readiness_report(self, applicant_name, visa_subclass, documents):
        """
        Generate a consolidated readiness report for an applicant.
        
        Args:
            applicant_name: Name of the applicant
            visa_subclass: The target visa subclass
            documents: List of analyzed document objects from the database
        """
        doc_summaries = []
        for doc in documents:
            doc_summaries.append({
                "file_name": doc.file_name,
                "type": doc.document_type,
                "status": doc.status,
                "score": doc.completeness_score,
                "summary": doc.ai_analysis.get('summary', 'No summary.') if doc.ai_analysis else 'No analysis.'
            })
            
        context = {
            'applicant_name': applicant_name,
            'visa_subclass': visa_subclass,
            'documents': doc_summaries
        }
        
        prompt = f"""Please provide a consolidated 'Application Readiness Report' for {applicant_name} who is applying for Visa Subclass {visa_subclass}.
        
        Analyze the status of the following uploaded documents:
        {json.dumps(doc_summaries, indent=2)}
        
        In your report, please include:
        1. **Executive Summary**: Overall readiness and confidence level.
        2. **Critical Gaps**: Highly important missing documents or major issues in uploaded ones.
        3. **Action Plan**: Specific, numbered steps the applicant must take next.
        4. **Submission Forecast**: How close they are to being ready to submit.
        """
        
        return self.chat(prompt, context=context)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

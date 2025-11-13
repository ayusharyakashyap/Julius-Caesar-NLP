"""
Phase 4: Prompt Engineering & Generation

This module handles:
1. System prompt design for Shakespearean Scholar persona
2. LLM generation using Google Gemini API
3. Context assembly and citation formatting
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()


class ShakespeareanScholar:
    """Expert Shakespearean Scholar persona using Gemini API"""
    
    SYSTEM_PROMPT = """You are an Expert Shakespearean Scholar with deep knowledge of William Shakespeare's works, particularly "The Tragedy of Julius Caesar." 

Your target audience is ICSE Class 10 students, so your answers must be:
1. **Academically Rigorous**: Demonstrate deep literary analysis and understanding
2. **Clear and Accessible**: Use language appropriate for Class 10 students
3. **Evidence-Based**: Always cite specific textual evidence from the play
4. **Insightful**: Go beyond surface-level answers to reveal deeper meanings

CRITICAL CONSTRAINTS:
- You MUST ONLY use information from the provided context chunks
- You MUST cite your sources by referencing the Act, Scene, and Speaker
- If the context doesn't contain enough information, say so explicitly
- Never make up quotes or fabricate information
- Maintain an academic yet encouraging tone

ANSWER STRUCTURE:
1. Direct answer to the question
2. Supporting evidence with citations (e.g., "As Brutus states in Act 2, Scene 1...")
3. Brief analysis or interpretation (when appropriate)
4. Connection to broader themes (for analytical questions)

Remember: You are a knowledgeable mentor helping students understand and appreciate Shakespeare's masterpiece."""

    def __init__(
        self,
        model_name: str = ""gemini-1.5-pro-latest"",
        temperature: float = 0.3,
        api_key: str = None
    ):
        """
        Initialize the Shakespearean Scholar
        
        Args:        ANONYMIZED_TELEMETRY=False
            model_name: Gemini model to use
            temperature: Lower = more focused, Higher = more creative
            api_key: Google API key (or set GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=self.api_key,
            convert_system_message_to_human=True
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "{query_with_context}")
        ])
    
    def format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context string"""
        context_parts = []
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            metadata = chunk.get('metadata', {})
            text = chunk.get('text', chunk.get('document', ''))
            
            act = metadata.get('act', '?')
            scene = metadata.get('scene', '?')
            speaker = metadata.get('speaker', '')
            chunk_type = metadata.get('type', '')
            
            # Format citation
            citation = f"[Source {i}: Act {act}, Scene {scene}"
            if speaker:
                citation += f", {speaker}"
            citation += f"]"
            
            context_parts.append(f"{citation}\n{text}\n")
        
        return "\n".join(context_parts)
    
    def create_query_with_context(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """Combine query with retrieved context"""
        context = self.format_context(retrieved_chunks)
        
        query_with_context = f"""CONTEXT FROM JULIUS CAESAR:
{context}

STUDENT QUESTION:
{query}

Please provide a comprehensive answer using ONLY the context provided above. Remember to cite your sources."""
        
        return query_with_context
    
    def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate answer using Gemini API
        
        Args:
            query: Student's question
            retrieved_chunks: List of relevant chunks from vector store
            
        Returns:
            Generated answer with citations
        """
        # Create query with context
        query_with_context = self.create_query_with_context(query, retrieved_chunks)
        
        # Generate answer
        messages = self.prompt_template.format_messages(
            query_with_context=query_with_context
        )
        
        response = self.model.invoke(messages)
        
        return response.content
    
    def generate_answer_streaming(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]]
    ):
        """
        Generate answer with streaming (for real-time UI)
        
        Args:
            query: Student's question
            retrieved_chunks: List of relevant chunks from vector store
            
        Yields:
            Tokens as they are generated
        """
        query_with_context = self.create_query_with_context(query, retrieved_chunks)
        
        messages = self.prompt_template.format_messages(
            query_with_context=query_with_context
        )
        
        for chunk in self.model.stream(messages):
            yield chunk.content


class FactualQAPrompt:
    """Specialized prompt for factual recall questions"""
    
    SYSTEM_PROMPT = """You are answering factual questions about "The Tragedy of Julius Caesar" by William Shakespeare.

For factual questions, provide:
1. A direct, concise answer
2. Specific textual evidence
3. Clear citation (Act, Scene, Speaker)

Keep answers brief and to the point for straightforward factual queries."""


class AnalyticalQAPrompt:
    """Specialized prompt for analytical/thematic questions"""
    
    SYSTEM_PROMPT = """You are providing literary analysis of "The Tragedy of Julius Caesar" by William Shakespeare.

For analytical questions, provide:
1. A clear thesis or main point
2. Multiple pieces of textual evidence
3. Deep analysis of literary devices, themes, or character development
4. Connections between different parts of the play
5. Consideration of historical and dramatic context

Your analysis should demonstrate sophisticated understanding while remaining accessible to Class 10 students."""


def create_scholar(
    scholar_type: str = "general",
    **kwargs
) -> ShakespeareanScholar:
    """
    Factory function to create different types of scholars
    
    Args:
        scholar_type: 'general', 'factual', or 'analytical'
        **kwargs: Additional arguments for ShakespeareanScholar
        
    Returns:
        ShakespeareanScholar instance
    """
    scholar = ShakespeareanScholar(**kwargs)
    
    if scholar_type == "factual":
        scholar.SYSTEM_PROMPT = FactualQAPrompt.SYSTEM_PROMPT
    elif scholar_type == "analytical":
        scholar.SYSTEM_PROMPT = AnalyticalQAPrompt.SYSTEM_PROMPT
    
    scholar.prompt_template = ChatPromptTemplate.from_messages([
        ("system", scholar.SYSTEM_PROMPT),
        ("human", "{query_with_context}")
    ])
    
    return scholar


def test_scholar():
    """Test the Shakespearean Scholar with sample queries"""
    print("=" * 60)
    print("Testing Shakespearean Scholar")
    print("=" * 60)
    
    # Create scholar
    scholar = ShakespeareanScholar()
    
    # Sample retrieved chunks (mock data)
    sample_chunks = [
        {
            'text': 'SOOTHSAYER: Beware the ides of March.',
            'metadata': {
                'act': 1,
                'scene': 2,
                'speaker': 'SOOTHSAYER',
                'type': 'dialogue'
            }
        },
        {
            'text': 'CAESAR: He is a dreamer. Let us leave him. Pass.',
            'metadata': {
                'act': 1,
                'scene': 2,
                'speaker': 'CAESAR',
                'type': 'dialogue'
            }
        }
    ]
    
    # Test query
    query = "What warning does the Soothsayer give to Caesar?"
    
    print(f"\nQuery: {query}\n")
    print("Generating answer...\n")
    
    answer = scholar.generate_answer(query, sample_chunks)
    
    print("Answer:")
    print("-" * 60)
    print(answer)
    print("-" * 60)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not found in environment variables")
        print("Please set it in a .env file or as an environment variable")
    else:
        test_scholar()

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part
from flask import current_app

def init_gemini():
    """Initialize Gemini client"""
    return genai.Client(api_key=current_app.config['GEMINI_API_KEY'])

def generate_response(prompt):
    """Generate response using Gemini with Google Search integration"""
    client = init_gemini()
    model_id = "gemini-2.0-flash-exp"
    
    # Initialize Google Search tool
    google_search_tool = Tool(
        google_search=GoogleSearch()
    )
    
    response = client.models.generate_content(
        model=model_id,
        contents=Part.from_text(prompt),
        config=GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
            tools=[google_search_tool],
            response_modalities=["TEXT"],
            max_output_tokens=100,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
    )
    
    if not response or not response.candidates:
        return "No response generated"
    
    # Combine the response text with search metadata
    result = response.candidates[0].content.parts[0].text
    
    # Add search sources if available
    if hasattr(response.candidates[0], 'grounding_metadata') and \
       hasattr(response.candidates[0].grounding_metadata, 'search_entry_point'):
        sources = response.candidates[0].grounding_metadata.search_entry_point.rendered_content
        result += "\n\nSources:\n" + sources
        
    return result

from google import genai
from google.genai import types
from flask import current_app

def init_gemini():
    """Initialize Gemini client"""
    return genai.Client(api_key=current_app.config['GEMINI_API_KEY'])

def generate_response(prompt):
    """Generate response using Gemini"""
    client = init_gemini()
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=types.Part.from_text(prompt),
        config=types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
            seed=5,
            max_output_tokens=100,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
    )
    
    return response.text if response else "No response generated"

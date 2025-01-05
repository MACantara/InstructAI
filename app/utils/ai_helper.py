from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part
from flask import current_app
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug logs are captured
logger.propagate = False

def init_gemini():
    """Initialize Gemini client"""
    logger.debug('Initializing Gemini client')
    try:
        client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        logger.info('Gemini client initialized successfully')
        return client
    except Exception as e:
        logger.error(f'Failed to initialize Gemini client: {str(e)}')
        raise

def generate_response(prompt):
    """Generate response using Gemini with Google Search integration"""
    logger.info(f'Generating response for prompt: "{prompt[:50]}..."')
    
    try:
        client = init_gemini()
        model_id = "gemini-2.0-flash-exp"
        
        logger.debug('Initializing Google Search tool')
        google_search_tool = Tool(
            google_search=GoogleSearch()
        )
        
        logger.debug('Configuring generation parameters')
        config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
            tools=[google_search_tool],
            response_modalities=["TEXT"],
            max_output_tokens=8192,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
        
        logger.debug('Sending request to Gemini API')
        response = client.models.generate_content(
            model=model_id,
            contents=Part.from_text(prompt),
            config=config
        )
        
        if not response or not response.candidates:
            logger.warning('No response generated from API')
            return "No response generated"
        
        logger.debug('Processing response and metadata')
        result = response.candidates[0].content.parts[0].text
        
        # Log response length for monitoring
        logger.debug(f'Response length: {len(result)} characters')
        
        if hasattr(response.candidates[0], 'grounding_metadata') and \
           hasattr(response.candidates[0].grounding_metadata, 'search_entry_point'):
            sources = response.candidates[0].grounding_metadata.search_entry_point.rendered_content
            logger.debug('Search sources found, appending to response')
            result += "\n\nSources:\n" + sources
        else:
            logger.debug('No search sources found in response')
        
        logger.info('Response generated successfully')
        return result
        
    except Exception as e:
        logger.error(f'Error generating response: {str(e)}', exc_info=True)
        raise

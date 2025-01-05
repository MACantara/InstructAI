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

def extract_search_metadata(response_candidate):
    """Extract and structure search metadata from response"""
    metadata = {}
    
    if hasattr(response_candidate, 'grounding_metadata'):
        meta = response_candidate.grounding_metadata
        
        # Extract grounding chunks focusing on web title and URI
        if meta.grounding_chunks:
            metadata['chunks'] = []
            logger.debug('Grounding chunks found:')
            for chunk in meta.grounding_chunks:
                chunk_data = chunk.model_dump()
                if 'web' in chunk_data:
                    web_data = {
                        'title': chunk_data['web'].get('title', 'Unknown title'),
                        'source': chunk_data['web'].get('uri', 'Unknown source')
                    }
                    metadata['chunks'].append(web_data)
                    logger.debug(f"Source: {web_data['title']} - {web_data['source']}")
    
    return metadata

def generate_syllabus_prompt(topic, include_objectives=True, include_readings=True):
    """Generate a structured prompt for syllabus creation"""
    prompt = f"""Create a comprehensive syllabus for a course on {topic}. 
Use Markdown formatting for better structure and readability.

Include the following sections:

# Course Description

# Course Structure

# Weekly Topics Breakdown (12-week format)
Use proper Markdown formatting with headers, lists, and emphasis where appropriate."""

    if include_objectives:
        prompt += "\n\n# Learning Objectives and Outcomes"
    
    if include_readings:
        prompt += "\n\n# Required and Recommended Readings"

    prompt += "\n\nEnsure proper Markdown formatting throughout the syllabus."
    return prompt

def generate_response(prompt_data):
    """Generate response using Gemini with Google Search integration"""
    logger.info(f'Generating syllabus for topic: "{prompt_data["topic"][:50]}..."')
    
    try:
        client = init_gemini()
        
        # Generate structured prompt
        full_prompt = generate_syllabus_prompt(
            prompt_data["topic"],
            prompt_data.get("include_objectives", True),
            prompt_data.get("include_readings", True)
        )
        
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
            contents=Part.from_text(full_prompt),
            config=config
        )
        
        if not response or not response.candidates:
            logger.warning('No response generated from API')
            return {"text": "No response generated", "metadata": {}}
        
        logger.debug('Processing response and metadata')
        result = response.candidates[0].content.parts[0].text
        
        # Log response length for monitoring
        logger.debug(f'Response length: {len(result)} characters')
        
        # Extract and structure metadata
        metadata = extract_search_metadata(response.candidates[0])
        
        return {
            "text": result,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f'Error generating response: {str(e)}', exc_info=True)
        raise

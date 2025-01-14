from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part
from flask import current_app
import logging
import json

logger = logging.getLogger(__name__)

def extract_content_metadata(response_candidate, week_number):
    """Extract metadata specific to weekly content"""
    metadata = {}
    
    if hasattr(response_candidate, 'grounding_metadata'):
        meta = response_candidate.grounding_metadata
        
        if meta.grounding_chunks:
            for chunk in meta.grounding_chunks:
                chunk_data = chunk.model_dump()
                if 'web' in chunk_data:
                    source_url = chunk_data['web'].get('uri')
                    source_title = chunk_data['web'].get('title')
                    
                    # Add source to appropriate section based on URL pattern
                    if 'youtube.com' in source_url or 'vimeo.com' in source_url:
                        if 'videos' not in metadata:
                            metadata['videos'] = []
                        metadata['videos'].append({
                            'title': source_title,
                            'url': source_url,
                            'description': f'Referenced in Week {week_number} content'
                        })
                    else:
                        if 'articles' not in metadata:
                            metadata['articles'] = []
                        metadata['articles'].append({
                            'title': source_title,
                            'url': source_url,
                            'relevance': f'Source material for Week {week_number}'
                        })
    
    return metadata

def generate_weekly_content(topic, week_data):
    """Generate detailed content for a specific weekly topic"""
    logger.debug(f"Received week data: {week_data}")
    
    if not week_data or not isinstance(week_data, dict):
        logger.error("Invalid week data format")
        return None
        
    try:
        prompt = f"""Generate comprehensive course content for Week {week_data.get('week', '?')}: {week_data.get('mainTopic', 'Unknown')}
        following this JSON structure:

        {{
            "week": {week_data.get('week', '?')},
            "topic": "{week_data.get('mainTopic', 'Unknown')}",
            "content": {{
                "lecture": {{
                    "notes": "Detailed lecture notes in markdown",
                    "slides": ["Key points for slides"],
                    "examples": ["Code or practical examples"]
                }},
                "resources": {{
                    "videos": [
                        {{
                            "title": "Video title",
                            "url": "Video URL",
                            "description": "Brief description"
                        }}
                    ],
                    "articles": [
                        {{
                            "title": "Article title",
                            "url": "Article URL",
                            "relevance": "Why this is important"
                        }}
                    ],
                    "tools": [
                        {{
                            "name": "Tool name",
                            "url": "Tool URL",
                            "purpose": "How it's used in this topic"
                        }}
                    ]
                }},
                "activities": {json.dumps(week_data.get('activities', []))},
                "quiz": {json.dumps(week_data.get('quiz', {}))},
                "exercises": [
                    {{
                        "title": "Exercise title",
                        "description": "Exercise description",
                        "difficulty": "beginner|intermediate|advanced",
                        "instructions": ["Step-by-step instructions"]
                    }}
                ]
            }}
        }}

        Use the following topics as guidance:
        {', '.join([t.get('subtitle', '') for t in week_data.get('topics', [])])}

        Quiz Information:
        Duration: {week_data.get('quiz', {}).get('duration', 'N/A')}
        Format: {week_data.get('quiz', {}).get('format', 'N/A')}
        Questions: {week_data.get('quiz', {}).get('numQuestions', 'N/A')}
        """

        client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        config = GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            candidate_count=1,
            tools=[Tool(google_search=GoogleSearch())],
            max_output_tokens=8192,
        )

        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=Part.from_text(prompt),
            config=config
        )

        if response and response.candidates:
            try:
                json_str = response.candidates[0].content.parts[0].text.strip()
                # Clean JSON string
                if not json_str.startswith('{'):
                    json_str = json_str[json_str.find('{'):]
                if not json_str.endswith('}'):
                    json_str = json_str[:json_str.rfind('}')+1]
                    
                content = json.loads(json_str)
                
                # Extract metadata and integrate with content
                metadata = extract_content_metadata(response.candidates[0], week_data.get('week'))
                
                # Update content with metadata sources
                if 'videos' in metadata:
                    content['content']['resources']['videos'].extend(metadata['videos'])
                
                if 'articles' in metadata:
                    content['content']['resources']['articles'].extend(metadata['articles'])
                
                logger.debug(f"Successfully generated content for week {week_data.get('week')} with {len(metadata.get('videos', []))} videos and {len(metadata.get('articles', []))} articles from metadata")
                return content
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Raw response: {json_str}")
                return None
        
        logger.warning("No response generated from API")
        return None
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        return None

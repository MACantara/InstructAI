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
        prompt = f"""You are an expert educational content developer with years of experience creating 
university-level course materials. Your expertise includes breaking down complex topics into 
digestible modules and creating engaging learning experiences.

TASK:
Generate comprehensive course content for Week {week_data.get('week', '?')} focused on: {week_data.get('mainTopic', 'Unknown')}

CONTEXT:
This is part of a {topic} course. The week covers the following subtopics:
{', '.join([t.get('subtitle', '') for t in week_data.get('topics', [])])}

APPROACH:
1. First, analyze the topic and identify key learning concepts
2. Then, create detailed lecture notes that build progressively
3. Next, extract key points for slides
4. Finally, develop practical examples and exercises

CONTENT REQUIREMENTS:
1. Lecture notes should be 500-750 words, using markdown formatting
2. Slides should contain 5-7 key points
3. Examples should be concrete and actionable
4. Resources should be highly relevant and diverse

OUTPUT FORMAT:
Use this exact JSON structure, maintaining all fields:
{{
    "week": {week_data.get('week', '?')},
    "topic": "{week_data.get('mainTopic', 'Unknown')}",
    "content": {{
        "lecture": {{
            "notes": "### [Main Topic]\\n\\nKey concepts and detailed explanations...\\n\\n### [Subtopic]\\n\\nDetailed breakdown...",
            "slides": [
                "Concise, actionable point 1",
                "Clear, memorable point 2"
            ],
            "examples": [
                "Specific, practical example with context",
                "Code or step-by-step demonstration"
            ]
        }},
        "resources": {{
            "videos": [
                {{
                    "title": "Clear, descriptive title",
                    "url": "URL",
                    "description": "1-2 sentences on relevance"
                }}
            ],
            "articles": [
                {{
                    "title": "Informative title",
                    "url": "URL",
                    "relevance": "Specific connection to topic"
                }}
            ],
            "tools": [
                {{
                    "name": "Tool name",
                    "url": "URL",
                    "purpose": "Specific use in this context"
                }}
            ]
        }},
        "activities": {json.dumps(week_data.get('activities', []))},
        "quiz": {json.dumps(week_data.get('quiz', {}))},
        "exercises": [
            {{
                "title": "Clear exercise title",
                "description": "2-3 sentences describing purpose",
                "difficulty": "beginner|intermediate|advanced",
                "instructions": [
                    "Step 1 with clear action",
                    "Step 2 with expected outcome"
                ]
            }}
        ]
    }}
}}

QUALITY CHECKLIST:
✓ Content builds on previous knowledge
✓ Examples are practical and relevant
✓ Instructions are clear and actionable
✓ Resources support learning objectives
✓ Exercises match topic difficulty

IMPORTANT:
- Ground your resource suggestions in real, authoritative sources
- Ensure all content directly supports learning objectives
- Balance theoretical knowledge with practical application
- Consider the quiz format: {week_data.get('quiz', {}).get('format', 'N/A')}
- Target content for a {week_data.get('quiz', {}).get('duration', 'N/A')} duration

Review and refine your response before submitting to ensure all requirements are met.
"""

        client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        config = GenerateContentConfig(
            temperature=1,
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

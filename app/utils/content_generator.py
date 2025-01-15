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
university-level course materials. Your expertise includes creating structured, hierarchical content
that builds knowledge systematically.

TASK:
Generate comprehensive course content for Week {week_data.get('week', '?')} focused on: {week_data.get('mainTopic', 'Unknown')}

CONTEXT:
This is part of a {topic} course. The week covers the following subtopics:
{', '.join([t.get('subtitle', '') for t in week_data.get('topics', [])])}

CONTENT STRUCTURE:
Your lecture notes must follow this exact hierarchical format:
1. Main Topic Title
   1.1. Major Point One
        - Comprehensive explanation
        - Key concepts
        - Related theories
   1.2. Major Point Two
        1.2.1. Subpoint A
               - Detailed breakdown
               - Examples
               - Applications
        1.2.2. Subpoint B
               - Specific details
               - Implementation
   1.3. Major Point Three
        - Supporting evidence
        - Practical applications

FORMATTING REQUIREMENTS:
1. Use markdown for all content
2. Each point must have 2-3 paragraphs of explanation
3. Include relevant examples after each major point
4. Use consistent numbering (1., 1.1., 1.1.1., etc.)
5. Bold key terms using **term**
6. Use > for important quotes or definitions
7. Use --- for section breaks

OUTPUT FORMAT:
Use this exact JSON structure:
{{
    "week": {week_data.get('week', '?')},
    "topic": "{week_data.get('mainTopic', 'Unknown')}",
    "content": {{
        "lecture": {{
            "notes": "# [Main Topic]\\n\\n1. First Major Point\\n1.1. Subpoint\\n- Detailed explanation...\\n\\n1.2. Subpoint\\n1.2.1. Further detail...\\n",
            "slides": [
                "Hierarchical bullet points matching lecture structure",
                "One slide per major section (1.1, 1.2, etc.)"
            ],
            "examples": [
                "Practical example following each major point",
                "Implementation details with steps"
            ]
        }},
        "resources": {{
            "videos": [
                {{
                    "title": "Title matching specific subtopic",
                    "url": "URL",
                    "description": "Which section (1.1, 1.2, etc.) this supports"
                }}
            ],
            "articles": [
                {{
                    "title": "Title aligned with specific points",
                    "url": "URL",
                    "relevance": "Which concepts (1.1, 1.2, etc.) this explains"
                }}
            ],
            "tools": [
                {{
                    "name": "Tool name",
                    "url": "URL",
                    "purpose": "Which section this supports"
                }}
            ]
        }},
        "activities": {json.dumps(week_data.get('activities', []))},
        "quiz": {json.dumps(week_data.get('quiz', {}))},
        "exercises": [
            {{
                "title": "Exercise aligned with section X.X",
                "description": "Practice for specific numbered points",
                "difficulty": "beginner|intermediate|advanced",
                "instructions": [
                    "Step 1 referencing specific concepts",
                    "Step 2 building on previous steps"
                ]
            }}
        ]
    }}
}}

QUALITY CHECKLIST:
✓ Each major point (1.1, 1.2, etc.) has comprehensive coverage
✓ Subpoints provide detailed breakdowns
✓ Examples directly relate to numbered sections
✓ Resources support specific numbered topics
✓ Clear progression through numbered points

Before submitting:
1. Verify all section numbers are correct
2. Ensure each major point has sufficient detail
3. Confirm examples match their sections
4. Check that activities and exercises reference specific numbered points

Quiz Integration:
- Format: {week_data.get('quiz', {}).get('format', 'N/A')}
- Duration: {week_data.get('quiz', {}).get('duration', 'N/A')}
- Questions: {week_data.get('quiz', {}).get('numQuestions', 'N/A')}

Structure each section to build towards quiz concepts while maintaining clear numerical organization.
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

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

def clean_json_string(json_str):
    """Clean and validate JSON string"""
    try:
        # Remove any leading/trailing whitespace
        json_str = json_str.strip()
        
        # Find the first { and last }
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            logger.error("No valid JSON object found in response")
            return None
            
        # Extract just the JSON object
        json_str = json_str[start_idx:end_idx + 1]
        
        # Verify it's valid JSON by parsing it
        json.loads(json_str)
        
        return json_str
    except Exception as e:
        logger.error(f"JSON cleaning failed: {str(e)}")
        logger.debug(f"Original string: {json_str}")
        return None

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
Generate comprehensive course content for Week {week_data['week']}: {week_data['mainTopic']}

CONTEXT:
This is part of a {topic} course focusing on {week_data['description']}

REQUIRED TOPIC STRUCTURE:
You must strictly follow this exact topic structure:

1. {week_data['topics'][0]['subtitle']}
   1.1. {week_data['topics'][0]['points'][0]}
        - Detailed explanation
        - Implementation examples
        - Best practices
   1.2. {week_data['topics'][0]['points'][1]}
        - Comprehensive coverage
        - Real-world applications
   1.3. {week_data['topics'][0]['points'][2]}
        - Thorough breakdown
        - Practical considerations

2. {week_data['topics'][1]['subtitle']}
   2.1. {week_data['topics'][1]['points'][0]}
        - Core concepts
        - Implementation strategies
   2.2. {week_data['topics'][1]['points'][1]}
        - Detailed mechanics
        - System design
   2.3. {week_data['topics'][1]['points'][2]}
        - Key principles
        - Design patterns

3. {week_data['topics'][2]['subtitle']}
   3.1. {week_data['topics'][2]['points'][0]}
        - Fundamental approaches
        - Implementation techniques
   3.2. {week_data['topics'][2]['points'][1]}
        - Design considerations
        - Best practices
   3.3. {week_data['topics'][2]['points'][2]}
        - System integration
        - Advanced concepts

FORMATTING REQUIREMENTS:
1. Use markdown for all content
2. Each point must have 2-3 paragraphs of explanation
3. Include relevant examples after each major point
4. Use consistent numbering (1., 1.1., 1.1.1., etc.)
5. Bold key terms using **term**
6. Use > for important quotes or definitions
7. Use --- for section breaks

REQUIRED ACTIVITIES:
Title: {week_data['activities'][0]['title']}
Duration: {week_data['activities'][0]['duration']}
Description: {week_data['activities'][0]['description']}

REQUIRED ASSIGNMENT:
Title: {week_data['assignments'][0]['title']}
Due: {week_data['assignments'][0]['dueDate']}
Weight: {week_data['assignments'][0]['weightage']}
Description: {week_data['assignments'][0]['description']}

OUTPUT FORMAT:
Use this exact JSON structure, ensuring all content aligns with the provided topics:
{{
    "week": {week_data['week']},
    "topic": "{week_data['mainTopic']}",
    "content": {{
        "lecture": {{
            "notes": "# {week_data['mainTopic']}\\n\\n[Structured content following the exact topic outline above]",
            "slides": [
                "One slide per major section, following the given structure",
                "Must cover all specified points in order"
            ],
            "examples": [
                "Examples must directly relate to the specified topics",
                "Practical implementations of given concepts"
            ]
        }},
        "resources": {{
            "videos": [
                {{
                    "title": "Title specifically related to one of the given topics",
                    "url": "URL",
                    "description": "How it relates to specific point"
                }}
            ],
            "articles": [
                {{
                    "title": "Title aligned with specific given topics",
                    "url": "URL",
                    "relevance": "Connection to specific point"
                }}
            ],
            "tools": [
                {{
                    "name": "Tool name",
                    "url": "URL",
                    "purpose": "Use in implementing specific concept"
                }}
            ]
        }},
        "activities": {json.dumps(week_data['activities'])},
        "quiz": {json.dumps(week_data['quiz'])},
        "exercises": [
            {{
                "title": "Exercise for specific topic section",
                "description": "Practice implementing covered concept",
                "difficulty": "beginner|intermediate|advanced",
                "instructions": [
                    "Step-by-step implementation",
                    "Based on covered material"
                ]
            }}
        ]
    }}
}}

QUALITY CHECKLIST:
✓ Content strictly follows provided topic structure
✓ All points from original structure are covered
✓ Examples relate to specified topics only
✓ Resources support given points
✓ Activities align with provided descriptions

Quiz Integration:
Format: {week_data['quiz']['format']}
Duration: {week_data['quiz']['duration']}
Questions: {week_data['quiz']['numQuestions']}
Points: {week_data['quiz']['totalPoints']}

Ensure all content directly supports these specific topics and builds toward the quiz requirements.
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
                raw_text = response.candidates[0].content.parts[0].text
                if not raw_text:
                    logger.error("Empty response from API")
                    return None
                
                logger.debug(f"Raw response length: {len(raw_text)}")
                json_str = clean_json_string(raw_text)
                
                if not json_str:
                    logger.error("Failed to clean JSON response")
                    return None
                    
                content = json.loads(json_str)
                
                # Add validation check
                if not isinstance(content, dict) or 'week' not in content:
                    logger.error("Invalid content structure")
                    return None
                
                # Extract metadata and integrate with content
                metadata = extract_content_metadata(response.candidates[0], week_data.get('week'))
                
                if 'content' not in content or 'resources' not in content['content']:
                    logger.error("Missing required content structure")
                    return None
                
                # Update content with metadata sources
                if 'videos' in metadata:
                    content['content']['resources']['videos'].extend(metadata['videos'])
                
                if 'articles' in metadata:
                    content['content']['resources']['articles'].extend(metadata['articles'])
                
                logger.debug(f"Successfully generated content for week {week_data.get('week')}")
                return content
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {str(e)}")
                logger.debug(f"Attempted to parse: {json_str if 'json_str' in locals() else 'No JSON string available'}")
                return None
            except Exception as e:
                logger.error(f"Content processing failed: {str(e)}")
                return None
        
        logger.warning("No response generated from API")
        return None
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        return None

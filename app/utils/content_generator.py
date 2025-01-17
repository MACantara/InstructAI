from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part
from flask import current_app
import logging
import json
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        return psycopg2.connect(
            os.getenv('POSTGRES_URL_NON_POOLING'),
            sslmode='require'
        )
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

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
        # Debug logging
        logger.debug("Raw string length: %d", len(json_str))
        logger.debug("First 100 chars: %s", json_str[:100])
        
        # Remove any markdown backticks
        json_str = json_str.replace('```json', '').replace('```', '')
        
        # Remove any leading/trailing whitespace
        json_str = json_str.strip()
        
        # Find the first { and last }
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            logger.error("No valid JSON object found in response")
            logger.debug("Full response: %s", json_str)
            return None
            
        # Extract just the JSON object
        json_str = json_str[start_idx:end_idx + 1]
        
        # Try to parse it to validate
        parsed = json.loads(json_str)
        if not isinstance(parsed, dict):
            logger.error("Parsed JSON is not an object")
            return None
            
        return json_str
        
    except Exception as e:
        logger.error(f"JSON cleaning failed: {str(e)}")
        logger.debug("Failed string: %s", json_str)
        return None

def store_weekly_content(course_id, week_data, generated_content):
    """Store generated weekly content in database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update or insert weekly topic content
        cur.execute("""
            UPDATE weekly_topics 
            SET content = content || %s
            WHERE course_id = %s AND week_number = %s
            RETURNING id
        """, (
            Json(generated_content),
            course_id,
            week_data['week']
        ))
        
        result = cur.fetchone()
        if not result:
            logger.error(f"No weekly topic found for course {course_id}, week {week_data['week']}")
            return None
            
        weekly_topic_id = result[0]
        
        # Store resources
        if 'resources' in generated_content['content']:
            resources = generated_content['content']['resources']
            
            # Store videos
            for video in resources.get('videos', []):
                cur.execute("""
                    INSERT INTO resources (weekly_topic_id, type, title, url, description)
                    VALUES (%s, 'video', %s, %s, %s)
                """, (weekly_topic_id, video['title'], video['url'], video['description']))
            
            # Store articles
            for article in resources.get('articles', []):
                cur.execute("""
                    INSERT INTO resources (weekly_topic_id, type, title, url, description)
                    VALUES (%s, 'article', %s, %s, %s)
                """, (weekly_topic_id, article['title'], article['url'], article.get('relevance', '')))
            
            # Store tools
            for tool in resources.get('tools', []):
                cur.execute("""
                    INSERT INTO resources (weekly_topic_id, type, title, url, description)
                    VALUES (%s, 'tool', %s, %s, %s)
                """, (weekly_topic_id, tool['name'], tool['url'], tool.get('purpose', '')))
        
        # Store key points
        if 'lecture' in generated_content['content']:
            lecture = generated_content['content']['lecture']
            
            # Store slides as key points
            for idx, point in enumerate(lecture.get('slides', [])):
                cur.execute("""
                    INSERT INTO key_points (weekly_topic_id, content, order_index)
                    VALUES (%s, %s, %s)
                """, (weekly_topic_id, point, idx))
            
            # Store examples
            for example in lecture.get('examples', []):
                title = None
                content = example
                
                # Check if example contains a title (separated by colon)
                if ':' in example:
                    title, content = example.split(':', 1)
                
                cur.execute("""
                    INSERT INTO examples (weekly_topic_id, title, content)
                    VALUES (%s, %s, %s)
                """, (weekly_topic_id, title, content.strip()))
        
        # Store practice exercises
        if 'exercises' in generated_content['content']:
            for exercise in generated_content['content']['exercises']:
                cur.execute("""
                    INSERT INTO practice_exercises 
                    (weekly_topic_id, title, description, difficulty, instructions)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    weekly_topic_id,
                    exercise['title'],
                    exercise['description'],
                    exercise['difficulty'],
                    Json(exercise.get('instructions', []))
                ))
        
        conn.commit()
        return weekly_topic_id
        
    except Exception as e:
        logger.error(f"Error storing weekly content: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def retrieve_weekly_content(weekly_topic_id):
    """Retrieve complete weekly content from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get main content
        cur.execute("""
            SELECT content FROM weekly_topics WHERE id = %s
        """, (weekly_topic_id,))
        content = cur.fetchone()
        
        if not content:
            return None
            
        result = content[0]
        
        # Get key points
        cur.execute("""
            SELECT content FROM key_points 
            WHERE weekly_topic_id = %s 
            ORDER BY order_index
        """, (weekly_topic_id,))
        key_points = [row[0] for row in cur.fetchall()]
        
        # Get examples
        cur.execute("""
            SELECT title, content FROM examples 
            WHERE weekly_topic_id = %s
        """, (weekly_topic_id,))
        examples = [{
            'title': row[0],
            'content': row[1]
        } for row in cur.fetchall()]
        
        # Get practice exercises
        cur.execute("""
            SELECT title, description, difficulty, instructions 
            FROM practice_exercises 
            WHERE weekly_topic_id = %s
        """, (weekly_topic_id,))
        exercises = [{
            'title': row[0],
            'description': row[1],
            'difficulty': row[2],
            'instructions': row[3]
        } for row in cur.fetchall()]
        
        # Merge all content
        if isinstance(result, dict):
            result['content']['lecture']['slides'] = key_points
            result['content']['examples'] = examples
            result['content']['exercises'] = exercises
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving weekly content: {str(e)}")
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def generate_weekly_content(topic, week_data, course_id):
    """Generate detailed content for a specific weekly topic"""
    logger.debug(f"Received week data: {week_data}")
    
    if not week_data or not isinstance(week_data, dict):
        logger.error("Invalid week data format")
        return None
        
    try:
        # Helper function to safely get nested values
        def safe_get_text(obj, *keys, default=""):
            try:
                value = obj
                for key in keys:
                    value = value[key]
                return str(value) if value is not None else default
            except (KeyError, TypeError, AttributeError):
                return default

        prompt = f"""You are an expert educational content developer with years of experience creating 
university-level course materials. Your expertise includes creating structured, hierarchical content
that builds knowledge systematically.

TASK:
Generate comprehensive course content for Week {safe_get_text(week_data, 'week')}: {safe_get_text(week_data, 'mainTopic')}

CONTEXT:
This is part of a {topic} course focusing on {safe_get_text(week_data, 'description')}

REQUIRED TOPIC STRUCTURE:
You must strictly follow this exact topic structure:

1. {safe_get_text(week_data, 'topics', 0, 'subtitle')}
   1.1. {safe_get_text(week_data, 'topics', 0, 'points', 0)}
        - Detailed explanation
        - Implementation examples
        - Best practices
   1.2. {safe_get_text(week_data, 'topics', 0, 'points', 1)}
        - Comprehensive coverage
        - Real-world applications
   1.3. {safe_get_text(week_data, 'topics', 0, 'points', 2)}
        - Thorough breakdown
        - Practical considerations

2. {safe_get_text(week_data, 'topics', 1, 'subtitle')}
   2.1. {safe_get_text(week_data, 'topics', 1, 'points', 0)}
        - Core concepts
        - Implementation strategies
   2.2. {safe_get_text(week_data, 'topics', 1, 'points', 1)}
        - Detailed mechanics
        - System design
   2.3. {safe_get_text(week_data, 'topics', 1, 'points', 2)}
        - Key principles
        - Design patterns

3. {safe_get_text(week_data, 'topics', 2, 'subtitle')}
   3.1. {safe_get_text(week_data, 'topics', 2, 'points', 0)}
        - Fundamental approaches
        - Implementation techniques
   3.2. {safe_get_text(week_data, 'topics', 2, 'points', 1)}
        - Design considerations
        - Best practices
   3.3. {safe_get_text(week_data, 'topics', 2, 'points', 2)}
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
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        client = genai.Client(api_key=api_key)
        config = GenerateContentConfig(
            temperature=0.7,  # Lower temperature for more structured output
            top_k=40,
            top_p=0.95,
            candidate_count=1,
            tools=[Tool(google_search=GoogleSearch())],
            max_output_tokens=8192,
            stop_sequences=["}"],  # Help ensure complete JSON
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
                
                logger.debug("Response received, length: %d", len(raw_text))
                
                # Try multiple cleaning attempts
                json_str = None
                cleaning_attempts = [
                    lambda x: clean_json_string(x),
                    lambda x: clean_json_string(x.split('\n', 1)[-1]),  # Skip potential header
                    lambda x: clean_json_string(x.partition('{')[2])  # Get everything after first {
                ]
                
                for attempt in cleaning_attempts:
                    json_str = attempt(raw_text)
                    if json_str:
                        break
                
                if not json_str:
                    logger.error("All JSON cleaning attempts failed")
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
                
                # Store in database
                weekly_topic_id = store_weekly_content(course_id, week_data, content)
                if weekly_topic_id:
                    content['weekly_topic_id'] = weekly_topic_id
                    logger.info(f"Successfully stored content for week {week_data.get('week')}")
                else:
                    logger.error("Failed to store weekly content in database")
                
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

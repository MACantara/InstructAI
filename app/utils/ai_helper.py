from google import genai
from google.genai.types import GenerateContentConfig, Part
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
logger.setLevel(logging.DEBUG)  # Ensure debug logs are captured
logger.propagate = False

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

def init_gemini():
    """Initialize Gemini client"""
    logger.debug('Initializing Gemini client')
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        client = genai.Client(api_key=api_key)
        logger.info('Gemini client initialized successfully')
        return client
    except Exception as e:
        logger.error(f'Failed to initialize Gemini client: {str(e)}')
        raise

def generate_syllabus_prompt(topic, include_objectives=True, include_readings=True):
    """Generate a structured prompt for syllabus creation"""
    prompt = f"""You are an experienced curriculum designer with expertise in creating comprehensive syllabi. 
Your task is to create a detailed, well-structured syllabus for '{topic}'.

STRICT REQUIREMENTS:
- Each week MUST have EXACTLY THREE subtopics
- Each subtopic MUST have AT LEAST THREE learning points
- Topics must progress logically from foundational to advanced concepts
- All content must be detailed and specific to the subject matter

STRUCTURE VALIDATION:
Your response will be rejected if:
1. Any week has fewer or more than 3 subtopics
2. Any subtopic has fewer than 3 points
3. Topics are too general or vague
4. Points lack specific, actionable content

Step 1: Analyze the topic and determine the appropriate scope and depth
Step 2: Structure the course content logically over 12 weeks
Step 3: Define clear learning objectives
Step 4: Select relevant readings and materials
Step 5: Format the output as valid JSON

Think carefully about each step before providing your response.

Output requirements:
- Provide ONLY valid JSON, no explanatory text
- Use specific, actionable language
- Keep descriptions concise but informative
- Ensure progression of topics builds on previous knowledge

Example structure for one week's content:
{{
    "week": 1,
    "mainTopic": "Introduction to Machine Learning",
    "description": "Foundational concepts and practical applications of machine learning, covering core principles, data handling, and basic algorithms",
    "topics": [
        {{
            "subtitle": "Fundamentals of Machine Learning",
            "points": [
                "Definition and historical development of machine learning",
                "Types of learning: supervised, unsupervised, and reinforcement",
                "Core terminology and basic mathematical concepts"
            ]
        }},
        {{
            "subtitle": "Data Preparation and Processing",
            "points": [
                "Data collection and cleaning methodologies",
                "Feature selection and engineering techniques",
                "Data normalization and standardization approaches"
            ]
        }},
        {{
            "subtitle": "Introduction to Learning Algorithms",
            "points": [
                "Basic linear regression and its applications",
                "Understanding cost functions and optimization",
                "Model evaluation metrics and validation techniques"
            ]
        }}
    ],
    "activities": [
        {{
            "type": "in-class exercise",
            "title": "string",
            "description": "string",
            "duration": "string (e.g. '30 minutes')"
        }}
    ],
    "assignments": [
        {{
            "title": "string",
            "description": "string",
            "dueDate": "string (e.g. 'End of Week 1')",
            "weightage": "string (e.g. '10%')"
        }}
    ]
}}

Generate a complete syllabus JSON using this schema:

{{
    "title": "{topic} Syllabus",
    "courseDescription": "string (max 200 words)",
    "courseStructure": {{
        "duration": "12 weeks",
        "format": "string (specify delivery method)",
        "assessment": "string (evaluation methods)"
    }},
    "weeklyTopics": [
        // Array of 12 week objects following example structure above
    ]"""

    if include_objectives:
        prompt += """,
    "learningObjectives": [
        "string (start with measurable action verbs)",
        "string (focus on demonstrable skills)"
    ]"""

    if include_readings:
        prompt += """,
    "readings": {{
        "required": [
            {{
                "title": "string (full title)",
                "author": "string (full name)",
                "description": "string (2-3 sentences)"
            }}
        ],
        "recommended": [
            {{
                "title": "string (full title)",
                "author": "string (full name)",
                "description": "string (2-3 sentences)"
            }}
        ]
    }}"""

    prompt += """}

Quality criteria:
1. Topics should progress logically from foundational to advanced concepts
2. Each week's content should be realistic to cover in the time allocated
3. Learning objectives must be specific and measurable
4. Reading selections should directly support the weekly topics

Before finalizing your response:
1. Verify all JSON syntax is valid
2. Check that all required fields are present
3. Ensure consistency between topics and objectives
4. Confirm readings align with course progression"""

    return prompt

def validate_json_structure(json_data):
    """Validate the JSON structure matches our expected schema"""
    required_fields = ['title', 'courseDescription', 'courseStructure', 'weeklyTopics']
    course_structure_fields = ['duration', 'format', 'assessment']
    weekly_topic_fields = ['week', 'mainTopic', 'description', 'topics', 'activities', 'assignments']

    try:
        # Check required top-level fields
        if not all(field in json_data for field in required_fields):
            logger.error(f"Missing required fields: {[f for f in required_fields if f not in json_data]}")
            return False

        # Validate course structure
        if not all(field in json_data['courseStructure'] for field in course_structure_fields):
            logger.error(f"Missing course structure fields: {[f for f in course_structure_fields if f not in json_data['courseStructure']]}")
            return False

        # Validate weekly topics
        if not isinstance(json_data['weeklyTopics'], list) or not json_data['weeklyTopics']:
            logger.error("weeklyTopics must be a non-empty list")
            return False

        for week in json_data['weeklyTopics']:
            # Check required week fields
            if not all(field in week for field in weekly_topic_fields):
                logger.error(f"Week {week.get('week', 'unknown')}: Missing required fields")
                return False

            # Strictly validate topic structure
            if not isinstance(week['topics'], list) or len(week['topics']) != 3:
                logger.error(f"Week {week.get('week')}: Must have exactly 3 topics")
                return False

            # Validate topics
            for topic in week['topics']:
                if not all(field in topic for field in ['subtitle', 'points']):
                    logger.error(f"Week {week.get('week')}: Topic missing required fields")
                    return False
                if not isinstance(topic['points'], list) or len(topic['points']) < 3:
                    logger.error(f"Topic '{topic.get('subtitle')}' must have at least 3 points")
                    return False

            # Validate activities and assignments
            if not isinstance(week.get('activities', []), list) or not isinstance(week.get('assignments', []), list):
                logger.error(f"Week {week.get('week')}: activities and assignments must be lists")
                return False

        return True

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def format_json_to_markdown(json_data):
    """Convert JSON structure to formatted Markdown"""
    markdown = f"# {json_data['title']}\n\n"
    
    markdown += "## Course Description\n"
    markdown += f"{json_data['courseDescription']}\n\n"
    
    markdown += "## Course Structure\n"
    markdown += f"**Duration:** {json_data['courseStructure']['duration']}\n"
    markdown += f"**Format:** {json_data['courseStructure']['format']}\n"
    markdown += f"**Assessment:** {json_data['courseStructure']['assessment']}\n\n"
    
    markdown += "## Weekly Topics\n"
    for week in json_data['weeklyTopics']:
        markdown += f"### Week {week['week']}: {week['mainTopic']}\n"
        markdown += f"{week['description']}\n\n"
        
        for topic in week['topics']:
            markdown += f"#### {topic['subtitle']}\n"
            for point in topic['points']:
                markdown += f"- {point}\n"
            markdown += "\n"
            
        if week['activities']:
            markdown += "#### In-Class Activities\n"
            for activity in week['activities']:
                markdown += f"- **{activity['title']}** ({activity['duration']})\n"
                markdown += f"  {activity['description']}\n"
            markdown += "\n"
            
        if week['assignments']:
            markdown += "#### Assignments\n"
            for assignment in week['assignments']:
                markdown += f"- **{assignment['title']}** (Due: {assignment['dueDate']}, Weight: {assignment['weightage']})\n"
                markdown += f"  {assignment['description']}\n"
            markdown += "\n"
    
    if 'learningObjectives' in json_data:
        markdown += "## Learning Objectives\n"
        for objective in json_data['learningObjectives']:
            markdown += f"- {objective}\n"
        markdown += "\n"
    
    if 'readings' in json_data:
        markdown += "## Required Readings\n"
        for reading in json_data['readings']['required']:
            markdown += f"- **{reading['title']}** by {reading['author']}\n"
            markdown += f"  {reading['description']}\n"
        markdown += "\n### Recommended Readings\n"
        for reading in json_data['readings']['recommended']:
            markdown += f"- **{reading['title']}** by {reading['author']}\n"
            markdown += f"  {reading['description']}\n"
    
    return markdown

def store_syllabus_in_db(json_data):
    """Store generated syllabus in database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert course data
        cur.execute("""
            INSERT INTO courses (title, description, structure)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (
            json_data['title'],
            json_data['courseDescription'],
            Json(json_data['courseStructure'])
        ))
        
        course_id = cur.fetchone()[0]
        
        # Insert weekly topics
        for week in json_data['weeklyTopics']:
            cur.execute("""
                INSERT INTO weekly_topics (course_id, week_number, main_topic, description, content)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                course_id,
                week['week'],
                week['mainTopic'],
                week['description'],
                Json(week)
            ))
            
            weekly_topic_id = cur.fetchone()[0]
            
            # Store activities
            for activity in week['activities']:
                cur.execute("""
                    INSERT INTO activities (weekly_topic_id, title, description, duration, type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    weekly_topic_id,
                    activity['title'],
                    activity['description'],
                    activity['duration'],
                    activity.get('type', 'in-class')
                ))
            
            # Store assignments
            for assignment in week['assignments']:
                cur.execute("""
                    INSERT INTO assignments (weekly_topic_id, title, description, due_date, weightage)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    weekly_topic_id,
                    assignment['title'],
                    assignment['description'],
                    assignment['dueDate'],
                    assignment['weightage']
                ))
        
        conn.commit()
        logger.info(f"Successfully stored course with ID: {course_id}")
        return course_id
        
    except Exception as e:
        logger.error(f"Database storage failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def generate_response(prompt_data):
    """Generate response using Gemini"""
    logger.info(f'Generating syllabus for topic: "{prompt_data["topic"][:50]}..."')
    
    try:
        client = init_gemini()
        
        # Generate structured prompt
        full_prompt = generate_syllabus_prompt(
            prompt_data["topic"],
            prompt_data.get("include_objectives", True),
            prompt_data.get("include_readings", True)
        )
        
        model_id = "gemma-3-27b-it"
        
        logger.debug('Configuring generation parameters')
        config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
            max_output_tokens=8192,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
        
        logger.debug('Sending request to Gemini API')
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt,
            config=config
        )
        
        if not response or not response.candidates:
            logger.warning('No response generated from API')
            return {"text": "No response generated"}
        
        result = response.candidates[0].content.parts[0].text
        
        try:
            # Clean the response to ensure it's valid JSON
            json_str = result.strip()
            if not json_str.startswith('{'):
                json_str = json_str[json_str.find('{'):]
            if not json_str.endswith('}'):
                json_str = json_str[:json_str.rfind('}')+1]

            # Parse and validate JSON
            json_data = json.loads(json_str)
            
            if not validate_json_structure(json_data):
                logger.warning('Invalid JSON structure, falling back to raw text')
                raise ValueError('Invalid JSON structure')

            # Convert JSON to formatted Markdown
            formatted_text = format_json_to_markdown(json_data)
            logger.info('Successfully parsed and validated JSON response')

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f'JSON parsing failed: {str(e)}, using raw text')
            formatted_text = result
        
        if 'json_data' in locals() and validate_json_structure(json_data):
            # Store in database
            course_id = store_syllabus_in_db(json_data)
            return {
                "text": formatted_text,
                "raw_json": json_data,
                "course_id": course_id
            }
        
        return {
            "text": formatted_text,
            "raw_json": json_data if 'json_data' in locals() else None
        }
        
    except Exception as e:
        logger.error(f'Error generating response: {str(e)}', exc_info=True)
        raise
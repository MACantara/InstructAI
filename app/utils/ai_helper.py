from google import genai
from google.genai.types import GenerateContentConfig, Part
from flask import current_app
import logging
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug logs are captured
logger.propagate = False

def get_db_connection():
    """Get MongoDB connection using environment variables"""
    try:
        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        db_name = os.getenv('DB_NAME', 'instructai')
        return client[db_name]
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

def generate_syllabus_prompt(topic):
    """Generate a structured prompt for university syllabus creation"""
    prompt = f"""You are an experienced university curriculum designer.
Your task is to create a comprehensive, university-style syllabus for the course: '{topic}'.

The syllabus MUST follow this exact JSON structure. Output ONLY valid JSON with no extra text.

STRUCTURE REQUIREMENTS:
- Group related content into week ranges (e.g., "1-2", "3", "4-5") — a major topic may span multiple weeks.
- Aim for a total of 16 weeks of content across all entries.
- Each entry MUST have 2–4 subtopics.
- courseOutcomes at the top level MUST have exactly 3 items: CO-1, CO-2, CO-3.
- Each weekly entry references one or more of CO-1, CO-2, CO-3 in its courseOutcomes array.
- kpi must be a single clear, measurable sentence starting with an action verb.
- learningActivities must list 2–4 specific activities.
- assessmentStrategies must list 2–3 specific assessment tools or methods.

JSON SCHEMA:
{{
  "title": "Full course title",
  "courseDescription": "2–3 sentence overview of the course.",
  "courseStructure": {{
    "duration": "16 weeks",
    "format": "e.g., 3-hour lecture + 2-hour lab per week",
    "assessment": "e.g., Quizzes 20%, Midterm 30%, Final Exam 30%, Projects 20%"
  }},
  "courseOutcomes": [
    {{"id": "CO-1", "description": "Recall and explain foundational concepts and principles of {topic}."}},
    {{"id": "CO-2", "description": "Apply techniques and methods of {topic} to solve practical problems."}},
    {{"id": "CO-3", "description": "Analyze, evaluate, and synthesize knowledge of {topic} to produce well-reasoned solutions."}}
  ],
  "weeklyTopics": [
    {{
      "weekRange": "1-2",
      "mainTopic": "Introduction and Foundations",
      "subtopics": [
        "History and overview of the field",
        "Core terminology and concepts",
        "Setting up the learning environment"
      ],
      "courseOutcomes": ["CO-1"],
      "kpi": "Identify and explain the core concepts and historical context of the subject.",
      "learningActivities": [
        "Interactive lecture with slide presentations",
        "Think-pair-share discussion on real-world applications",
        "Lab: Environment setup and exploratory exercise"
      ],
      "assessmentStrategies": [
        "Short written quiz on terminology",
        "Lab completion checklist"
      ]
    }}
  ]
}}

Fill in ALL weekly topics for a full 16-week course following the exact schema above.
Before outputting, verify:
1. JSON is syntactically valid.
2. All required fields are present in every entry.
3. weekRange values cover exactly 16 weeks total.
4. courseOutcomes references only CO-1, CO-2, or CO-3."""

    return prompt

def validate_json_structure(json_data):
    """Validate the JSON structure matches the university syllabus schema"""
    required_fields = ['title', 'courseDescription', 'courseStructure', 'courseOutcomes', 'weeklyTopics']
    course_structure_fields = ['duration', 'format', 'assessment']
    weekly_topic_fields = ['weekRange', 'mainTopic', 'subtopics', 'courseOutcomes', 'kpi', 'learningActivities', 'assessmentStrategies']

    try:
        # Check required top-level fields
        if not all(field in json_data for field in required_fields):
            logger.error(f"Missing required fields: {[f for f in required_fields if f not in json_data]}")
            return False

        # Validate course structure
        if not all(field in json_data['courseStructure'] for field in course_structure_fields):
            logger.error(f"Missing course structure fields: {[f for f in course_structure_fields if f not in json_data['courseStructure']]}")
            return False

        # Validate course outcomes
        if not isinstance(json_data['courseOutcomes'], list) or len(json_data['courseOutcomes']) < 1:
            logger.error("courseOutcomes must be a non-empty list")
            return False

        # Validate weekly topics
        if not isinstance(json_data['weeklyTopics'], list) or not json_data['weeklyTopics']:
            logger.error("weeklyTopics must be a non-empty list")
            return False

        valid_co_ids = {co['id'] for co in json_data['courseOutcomes']}

        for entry in json_data['weeklyTopics']:
            # Check required entry fields
            missing = [f for f in weekly_topic_fields if f not in entry]
            if missing:
                logger.error(f"Entry '{entry.get('weekRange', 'unknown')}': Missing fields {missing}")
                return False

            if not isinstance(entry['subtopics'], list) or len(entry['subtopics']) < 1:
                logger.error(f"Entry '{entry.get('weekRange')}': subtopics must be a non-empty list")
                return False

            if not isinstance(entry['courseOutcomes'], list) or len(entry['courseOutcomes']) < 1:
                logger.error(f"Entry '{entry.get('weekRange')}': courseOutcomes must be a non-empty list")
                return False

            if not isinstance(entry['learningActivities'], list) or len(entry['learningActivities']) < 1:
                logger.error(f"Entry '{entry.get('weekRange')}': learningActivities must be a non-empty list")
                return False

            if not isinstance(entry['assessmentStrategies'], list) or len(entry['assessmentStrategies']) < 1:
                logger.error(f"Entry '{entry.get('weekRange')}': assessmentStrategies must be a non-empty list")
                return False

        return True

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def format_json_to_markdown(json_data):
    """Convert university syllabus JSON to formatted Markdown"""
    markdown = f"# {json_data['title']}\n\n"

    markdown += "## Course Description\n"
    markdown += f"{json_data['courseDescription']}\n\n"

    markdown += "## Course Structure\n"
    markdown += f"**Duration:** {json_data['courseStructure']['duration']}\n"
    markdown += f"**Format:** {json_data['courseStructure']['format']}\n"
    markdown += f"**Assessment:** {json_data['courseStructure']['assessment']}\n\n"

    markdown += "## Course Outcomes\n"
    for co in json_data.get('courseOutcomes', []):
        markdown += f"- **{co['id']}:** {co['description']}\n"
    markdown += "\n"

    markdown += "## Course Schedule\n\n"
    markdown += "| Week | Main Topic & Subtopics | CO | KPI | Learning Activities | Assessment Strategies |\n"
    markdown += "|------|----------------------|-----|-----|--------------------|-----------------------|\n"
    for entry in json_data['weeklyTopics']:
        subtopics = '<br>'.join(f"- {s}" for s in entry['subtopics'])
        cos = ', '.join(entry['courseOutcomes'])
        activities = '<br>'.join(f"- {a}" for a in entry['learningActivities'])
        strategies = '<br>'.join(f"- {s}" for s in entry['assessmentStrategies'])
        markdown += f"| Week {entry['weekRange']} | **{entry['mainTopic']}**<br>{subtopics} | {cos} | {entry['kpi']} | {activities} | {strategies} |\n"

    return markdown

def store_syllabus_in_db(json_data):
    """Store generated syllabus in MongoDB"""
    try:
        db = get_db_connection()

        course_doc = {
            "title": json_data['title'],
            "description": json_data['courseDescription'],
            "structure": json_data['courseStructure'],
            "courseOutcomes": json_data.get('courseOutcomes', []),
            "weeklyTopics": json_data['weeklyTopics'],
            "createdAt": datetime.utcnow()
        }

        result = db.courses.insert_one(course_doc)
        course_id = str(result.inserted_id)
        
        logger.info(f"Successfully stored course with ID: {course_id}")
        return course_id
        
    except Exception as e:
        logger.error(f"MongoDB storage failed: {str(e)}")
        raise

def generate_response(prompt_data):
    """Generate response using Gemini"""
    logger.info(f'Generating syllabus for topic: "{prompt_data["topic"][:50]}..."')
    
    try:
        client = init_gemini()
        
        # Generate structured prompt
        full_prompt = generate_syllabus_prompt(prompt_data["topic"])
        
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
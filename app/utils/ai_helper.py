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
    """Generate a structured prompt for university syllabus creation with CLO-PLO and LLO-CLO alignment"""
    prompt = f"""You are an experienced university curriculum designer.
Your task is to create a comprehensive, university-style syllabus for the course: '{topic}'.

Output ONLY valid JSON with absolutely no extra text, markdown fences, or explanations.

═══════════════════════════════════════════════
GLOBAL STRUCTURE RULES
═══════════════════════════════════════════════
1. programOutcomes: exactly 5 items (PLO-1 through PLO-5). Use realistic, programme-level statements.
2. courseLearningOutcomes (CLOs): exactly 5 items (CLO-1 through CLO-5).
   - Each CLO must have a "ploAlignment" array referencing 1–3 of the PLO ids.
   - CLO descriptions must be specific to '{topic}' and use Bloom's taxonomy verbs.
3. weeklyTopics: cover exactly 18 weeks total using weekRange spans (e.g. "1", "1-2", "3-4").
   - Each entry has 2–4 subtopics.
   - Each entry has a "cloAlignment" array referencing 1–3 CLO ids.
   - Each entry has a "lessonLearningOutcomes" array with 2–3 LLO objects.
     * Each LLO has: "id" (e.g. "LLO-1.1"), "description", and "cloAlignment" (array of 1–2 CLO ids).
     * LLO ids use the format "LLO-<entryIndex>.<lloIndex>" (both 1-based).
   - kpi: one measurable sentence starting with an action verb.
   - learningActivities: 2–4 specific activities.
   - assessmentStrategies: 2–3 specific tools or methods.

═══════════════════════════════════════════════
EXACT JSON SCHEMA (fill ALL fields)
═══════════════════════════════════════════════
{{
  "title": "Full official course title",
  "courseDescription": "2–3 sentence overview.",
  "courseStructure": {{
    "duration": "18 weeks",
    "format": "e.g., 3-hour lecture + 2-hour lab per week",
    "assessment": "e.g., Quizzes 20%, Midterm 25%, Final Exam 35%, Projects 20%"
  }},
  "programOutcomes": [
    {{"id": "PLO-1", "description": "Apply knowledge of mathematics and science to engineering or technical problems."}},
    {{"id": "PLO-2", "description": "Design and conduct experiments, then analyze and interpret data."}},
    {{"id": "PLO-3", "description": "Design systems, components, or processes to meet desired needs."}},
    {{"id": "PLO-4", "description": "Communicate effectively in written, oral, and visual forms."}},
    {{"id": "PLO-5", "description": "Engage in lifelong learning and adapt to emerging technologies."}}
  ],
  "courseLearningOutcomes": [
    {{
      "id": "CLO-1",
      "description": "Recall and describe the foundational theories and principles of {topic}.",
      "ploAlignment": ["PLO-1", "PLO-5"]
    }},
    {{
      "id": "CLO-2",
      "description": "Apply core methods and tools of {topic} to analyse structured problems.",
      "ploAlignment": ["PLO-1", "PLO-2"]
    }},
    {{
      "id": "CLO-3",
      "description": "Design solutions or artefacts that address practical challenges within {topic}.",
      "ploAlignment": ["PLO-3"]
    }},
    {{
      "id": "CLO-4",
      "description": "Evaluate and critique approaches in {topic} using evidence-based reasoning.",
      "ploAlignment": ["PLO-2", "PLO-4"]
    }},
    {{
      "id": "CLO-5",
      "description": "Synthesise knowledge and independently pursue advanced topics in {topic}.",
      "ploAlignment": ["PLO-4", "PLO-5"]
    }}
  ],
  "weeklyTopics": [
    {{
      "weekRange": "1-2",
      "mainTopic": "Introduction and Foundations",
      "subtopics": [
        "History and context of {topic}",
        "Core terminology and conceptual framework",
        "Tools and environment setup"
      ],
      "cloAlignment": ["CLO-1"],
      "lessonLearningOutcomes": [
        {{
          "id": "LLO-1.1",
          "description": "Explain the historical development and significance of {topic}.",
          "cloAlignment": ["CLO-1"]
        }},
        {{
          "id": "LLO-1.2",
          "description": "Define and use core terminology accurately in context.",
          "cloAlignment": ["CLO-1"]
        }}
      ],
      "kpi": "Identify and explain the foundational concepts and historical context of {topic}.",
      "learningActivities": [
        "Lecture with contextualised slide deck",
        "Think-pair-share discussion on real-world relevance",
        "Lab: Environment setup and guided exploration"
      ],
      "assessmentStrategies": [
        "Terminology quiz (MCQ)",
        "Lab completion checklist and reflection note"
      ]
    }}
  ]
}}

VERIFICATION CHECKLIST — confirm before outputting:
1. JSON is syntactically valid (no trailing commas, no comments).
2. weeklyTopics spans exactly 18 weeks.
3. Every CLO has ploAlignment referencing existing PLO ids.
4. Every LLO has cloAlignment referencing existing CLO ids.
5. Every weeklyTopic entry has cloAlignment referencing existing CLO ids.
6. All required fields present in every object."""

    return prompt

def validate_json_structure(json_data):
    """Validate the JSON structure matches the university syllabus schema with CLO/PLO/LLO"""
    required_top = ['title', 'courseDescription', 'courseStructure',
                    'programOutcomes', 'courseLearningOutcomes', 'weeklyTopics']
    course_structure_fields = ['duration', 'format', 'assessment']
    weekly_topic_fields = ['weekRange', 'mainTopic', 'subtopics', 'cloAlignment',
                           'lessonLearningOutcomes', 'kpi', 'learningActivities', 'assessmentStrategies']

    try:
        # Check required top-level fields
        missing_top = [f for f in required_top if f not in json_data]
        if missing_top:
            logger.error(f"Missing top-level fields: {missing_top}")
            return False

        # Validate course structure
        if not all(f in json_data['courseStructure'] for f in course_structure_fields):
            logger.error(f"Missing courseStructure fields: {[f for f in course_structure_fields if f not in json_data['courseStructure']]}")
            return False

        # Validate programme outcomes
        if not isinstance(json_data['programOutcomes'], list) or len(json_data['programOutcomes']) < 1:
            logger.error("programOutcomes must be a non-empty list")
            return False

        # Validate CLOs
        if not isinstance(json_data['courseLearningOutcomes'], list) or len(json_data['courseLearningOutcomes']) < 1:
            logger.error("courseLearningOutcomes must be a non-empty list")
            return False

        valid_plo_ids = {p['id'] for p in json_data['programOutcomes']}
        for clo in json_data['courseLearningOutcomes']:
            if not all(f in clo for f in ['id', 'description', 'ploAlignment']):
                logger.error(f"CLO missing required fields: {clo.get('id', 'unknown')}")
                return False
            bad_plos = [p for p in clo['ploAlignment'] if p not in valid_plo_ids]
            if bad_plos:
                logger.warning(f"CLO '{clo['id']}' references unknown PLOs: {bad_plos}")

        # Validate weekly topics
        if not isinstance(json_data['weeklyTopics'], list) or not json_data['weeklyTopics']:
            logger.error("weeklyTopics must be a non-empty list")
            return False

        valid_clo_ids = {c['id'] for c in json_data['courseLearningOutcomes']}

        for entry in json_data['weeklyTopics']:
            wr = entry.get('weekRange', 'unknown')
            missing = [f for f in weekly_topic_fields if f not in entry]
            if missing:
                logger.error(f"Entry Week {wr}: Missing fields {missing}")
                return False

            if not isinstance(entry['subtopics'], list) or len(entry['subtopics']) < 1:
                logger.error(f"Entry Week {wr}: subtopics must be a non-empty list")
                return False

            if not isinstance(entry['cloAlignment'], list) or len(entry['cloAlignment']) < 1:
                logger.error(f"Entry Week {wr}: cloAlignment must be a non-empty list")
                return False

            if not isinstance(entry['lessonLearningOutcomes'], list) or len(entry['lessonLearningOutcomes']) < 1:
                logger.error(f"Entry Week {wr}: lessonLearningOutcomes must be a non-empty list")
                return False

            for llo in entry['lessonLearningOutcomes']:
                if not all(f in llo for f in ['id', 'description', 'cloAlignment']):
                    logger.error(f"Entry Week {wr}: LLO missing required fields")
                    return False

            if not isinstance(entry['learningActivities'], list) or len(entry['learningActivities']) < 1:
                logger.error(f"Entry Week {wr}: learningActivities must be a non-empty list")
                return False

            if not isinstance(entry['assessmentStrategies'], list) or len(entry['assessmentStrategies']) < 1:
                logger.error(f"Entry Week {wr}: assessmentStrategies must be a non-empty list")
                return False

        return True

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def format_json_to_markdown(json_data):
    """Convert university syllabus JSON (CLO/PLO/LLO schema) to formatted Markdown"""
    markdown = f"# {json_data['title']}\n\n"

    markdown += "## Course Description\n"
    markdown += f"{json_data['courseDescription']}\n\n"

    markdown += "## Course Structure\n"
    markdown += f"**Duration:** {json_data['courseStructure']['duration']}\n"
    markdown += f"**Format:** {json_data['courseStructure']['format']}\n"
    markdown += f"**Assessment:** {json_data['courseStructure']['assessment']}\n\n"

    # Programme Learning Outcomes
    markdown += "## Programme Learning Outcomes (PLOs)\n"
    for plo in json_data.get('programOutcomes', []):
        markdown += f"- **{plo['id']}:** {plo['description']}\n"
    markdown += "\n"

    # Course Learning Outcomes
    clos = json_data.get('courseLearningOutcomes', [])
    markdown += "## Course Learning Outcomes (CLOs)\n"
    for clo in clos:
        plo_refs = ', '.join(clo.get('ploAlignment', []))
        markdown += f"- **{clo['id']}** [{plo_refs}]: {clo['description']}\n"
    markdown += "\n"

    # CLO-PLO Alignment Matrix
    plos = json_data.get('programOutcomes', [])
    if clos and plos:
        plo_ids = [p['id'] for p in plos]
        markdown += "## CLO-PLO Alignment Matrix\n\n"
        header = "| CLO | " + " | ".join(plo_ids) + " |\n"
        sep = "|-----" + "|".join(["------"] * len(plo_ids)) + "|\n"
        markdown += header + sep
        for clo in clos:
            aligned = set(clo.get('ploAlignment', []))
            cells = " | ".join("✓" if pid in aligned else "" for pid in plo_ids)
            markdown += f"| {clo['id']} | {cells} |\n"
        markdown += "\n"

    # Course Schedule
    markdown += "## Course Schedule\n\n"
    markdown += "| Week | Main Topic & Subtopics | LLOs | CLO | KPI | Learning Activities | Assessment Strategies |\n"
    markdown += "|------|----------------------|------|-----|-----|--------------------|-----------------------|\n"
    for entry in json_data['weeklyTopics']:
        subtopics = '<br>'.join(f"- {s}" for s in entry['subtopics'])
        llos = '<br>'.join(
            f"{l['id']}: {l['description']}" for l in entry.get('lessonLearningOutcomes', [])
        )
        clo_refs = ', '.join(entry.get('cloAlignment', []))
        activities = '<br>'.join(f"- {a}" for a in entry['learningActivities'])
        strategies = '<br>'.join(f"- {s}" for s in entry['assessmentStrategies'])
        markdown += f"| Week {entry['weekRange']} | **{entry['mainTopic']}**<br>{subtopics} | {llos} | {clo_refs} | {entry['kpi']} | {activities} | {strategies} |\n"
    markdown += "\n"

    # LLO-CLO Alignment Matrix
    if clos:
        clo_ids = [c['id'] for c in clos]
        markdown += "## LLO-CLO Alignment Matrix\n\n"
        header = "| LLO | " + " | ".join(clo_ids) + " |\n"
        sep = "|-----" + "|".join(["------"] * len(clo_ids)) + "|\n"
        markdown += header + sep
        for entry in json_data['weeklyTopics']:
            for llo in entry.get('lessonLearningOutcomes', []):
                aligned = set(llo.get('cloAlignment', []))
                cells = " | ".join("✓" if cid in aligned else "" for cid in clo_ids)
                markdown += f"| {llo['id']} | {cells} |\n"
        markdown += "\n"

    return markdown

def store_syllabus_in_db(json_data):
    """Store generated syllabus in MongoDB"""
    try:
        db = get_db_connection()

        course_doc = {
            "title": json_data['title'],
            "description": json_data['courseDescription'],
            "structure": json_data['courseStructure'],
            "programOutcomes": json_data.get('programOutcomes', []),
            "courseLearningOutcomes": json_data.get('courseLearningOutcomes', []),
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
            max_output_tokens=16384,
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
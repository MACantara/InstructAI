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

def generate_syllabus_prompt(
    course_title,
    course_code,
    duration_weeks,
    lecture_hours,
    lab_hours,
    topic_context,
    graduate_attributes_input,
    peos_input,
    plos_input
):
    """Generate a structured prompt for university syllabus creation with GA/PEO/PLO/CLO/LLO alignment."""
    prompt = f"""You are an experienced university curriculum designer.
Your task is to create a comprehensive, university-style syllabus for course '{course_code} - {course_title}'.
Topic context: '{topic_context or course_title}'.

Output ONLY valid JSON with absolutely no extra text, markdown fences, or explanations.

═══════════════════════════════════════════════
GLOBAL STRUCTURE RULES
═══════════════════════════════════════════════
1. The following three sections MUST be derived from user-provided content only.
    Do NOT invent, rewrite, or add new items beyond what the user provided:
    - graduateAttributes
    - programEducationalObjectives (PEOs)
    - programOutcomes (PLOs)
2. Convert the user input into the required JSON schema as faithfully as possible.
    Keep wording and intent of user input intact while only normalizing into valid JSON fields.
3. For graduateAttributes, map items into exactly these sections:
    - Character
    - Competence
    - Commitment to Service
4. For PEOs, include ids and graduateAttributeAlignment based on the user input.
5. For PLOs, include ids and peoAlignment based on the user input.
4. courseLearningOutcomes (CLOs): exactly 5 items (CLO-1 through CLO-5).
   - Each CLO must have a "ploAlignment" array referencing 1–3 of the PLO ids.
    - CLO descriptions must be specific to '{topic_context or course_title}' and use Bloom's taxonomy verbs.
5. weeklyTopics: cover exactly {duration_weeks} weeks total using weekRange spans (e.g. "1", "1-2", "3-4").
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
    "title": "{course_title}",
    "courseCode": "{course_code}",
  "courseDescription": "2–3 sentence overview.",
  "courseStructure": {{
        "duration": "{duration_weeks} weeks",
        "format": "{lecture_hours}-hour lecture + {lab_hours}-hour laboratory per week"
    }},
    "timeFramePerWeek": {{
        "lectureHours": {lecture_hours},
        "laboratoryHours": {lab_hours}
    }},
    "graduateAttributes": {{
        "Character": [
            "Demonstrates integrity and professional ethics in decision-making."
        ],
        "Competence": [
            "Applies disciplinary knowledge and technical skills to solve real-world problems."
        ],
        "Commitment to Service": [
            "Contributes to community and national development through responsible practice."
        ]
    }},
    "programEducationalObjectives": [
        {{
            "id": "PEO-1",
            "description": "Build and apply strong disciplinary foundations in professional contexts.",
            "graduateAttributeAlignment": ["Competence"]
        }},
        {{
            "id": "PEO-2",
            "description": "Lead with ethical character and collaborative professionalism.",
            "graduateAttributeAlignment": ["Character"]
        }},
        {{
            "id": "PEO-3",
            "description": "Serve society through innovation and sustainable practice.",
            "graduateAttributeAlignment": ["Commitment to Service"]
        }}
  }},
  "programOutcomes": [
        {{"id": "PLO-1", "description": "Apply knowledge of mathematics and science to engineering or technical problems.", "peoAlignment": ["PEO-1"]}},
        {{"id": "PLO-2", "description": "Design and conduct experiments, then analyze and interpret data.", "peoAlignment": ["PEO-1", "PEO-3"]}},
        {{"id": "PLO-3", "description": "Design systems, components, or processes to meet desired needs.", "peoAlignment": ["PEO-1", "PEO-3"]}},
        {{"id": "PLO-4", "description": "Communicate effectively in written, oral, and visual forms.", "peoAlignment": ["PEO-2"]}},
        {{"id": "PLO-5", "description": "Engage in lifelong learning and adapt to emerging technologies.", "peoAlignment": ["PEO-2", "PEO-3"]}}
  ],
  "courseLearningOutcomes": [
    {{
      "id": "CLO-1",
            "description": "Recall and describe the foundational theories and principles of {topic_context or course_title}.",
      "ploAlignment": ["PLO-1", "PLO-5"]
    }},
    {{
      "id": "CLO-2",
            "description": "Apply core methods and tools of {topic_context or course_title} to analyse structured problems.",
      "ploAlignment": ["PLO-1", "PLO-2"]
    }},
    {{
      "id": "CLO-3",
            "description": "Design solutions or artefacts that address practical challenges within {topic_context or course_title}.",
      "ploAlignment": ["PLO-3"]
    }},
    {{
      "id": "CLO-4",
            "description": "Evaluate and critique approaches in {topic_context or course_title} using evidence-based reasoning.",
      "ploAlignment": ["PLO-2", "PLO-4"]
    }},
    {{
      "id": "CLO-5",
            "description": "Synthesise knowledge and independently pursue advanced topics in {topic_context or course_title}.",
      "ploAlignment": ["PLO-4", "PLO-5"]
    }}
  ],
  "weeklyTopics": [
    {{
      "weekRange": "1-2",
      "mainTopic": "Introduction and Foundations",
      "subtopics": [
                "History and context of {topic_context or course_title}",
        "Core terminology and conceptual framework",
        "Tools and environment setup"
      ],
      "cloAlignment": ["CLO-1"],
      "lessonLearningOutcomes": [
        {{
          "id": "LLO-1.1",
                    "description": "Explain the historical development and significance of {topic_context or course_title}.",
          "cloAlignment": ["CLO-1"]
        }},
        {{
          "id": "LLO-1.2",
          "description": "Define and use core terminology accurately in context.",
          "cloAlignment": ["CLO-1"]
        }}
      ],
            "kpi": "Identify and explain the foundational concepts and historical context of {topic_context or course_title}.",
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

USER-PROVIDED CONTENT (USE THIS INSTEAD OF GENERATING NEW GA/PEO/PLO CONTENT)
Graduate Attributes input:
{graduate_attributes_input or 'No Graduate Attributes input provided.'}

PEOs input:
{peos_input or 'No PEO input provided.'}

PLOs input:
{plos_input or 'No PLO input provided.'}

VERIFICATION CHECKLIST — confirm before outputting:
1. JSON is syntactically valid (no trailing commas, no comments).
2. weeklyTopics spans exactly {duration_weeks} weeks.
3. Every PEO has graduateAttributeAlignment with valid Graduate Attribute section names.
4. Every PLO has peoAlignment referencing existing PEO ids.
5. Every CLO has ploAlignment referencing existing PLO ids.
6. Every LLO has cloAlignment referencing existing CLO ids.
7. Every weeklyTopic entry has cloAlignment referencing existing CLO ids.
8. All required fields present in every object."""

    return prompt

def validate_json_structure(json_data):
    """Validate the JSON structure matches the university syllabus schema with GA/PEO/PLO/CLO/LLO."""
    required_top = ['title', 'courseDescription', 'courseStructure',
                    'graduateAttributes', 'programEducationalObjectives',
                    'programOutcomes', 'courseLearningOutcomes', 'weeklyTopics']
    course_structure_fields = ['duration', 'format']
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

        # Validate graduate attributes
        ga = json_data['graduateAttributes']
        required_ga_sections = ['Character', 'Competence', 'Commitment to Service']
        if not isinstance(ga, dict) or not all(section in ga for section in required_ga_sections):
            logger.error("graduateAttributes must include Character, Competence, and Commitment to Service")
            return False

        # Validate PEOs
        peos = json_data['programEducationalObjectives']
        if not isinstance(peos, list) or len(peos) < 1:
            logger.error("programEducationalObjectives must be a non-empty list")
            return False

        valid_peo_ids = {p['id'] for p in peos if 'id' in p}
        for peo in peos:
            if not all(f in peo for f in ['id', 'description', 'graduateAttributeAlignment']):
                logger.error(f"PEO missing required fields: {peo.get('id', 'unknown')}")
                return False
            bad_ga = [a for a in peo['graduateAttributeAlignment'] if a not in required_ga_sections]
            if bad_ga:
                logger.warning(f"PEO '{peo['id']}' references unknown Graduate Attributes: {bad_ga}")

        # Validate CLOs
        if not isinstance(json_data['courseLearningOutcomes'], list) or len(json_data['courseLearningOutcomes']) < 1:
            logger.error("courseLearningOutcomes must be a non-empty list")
            return False

        valid_plo_ids = {p['id'] for p in json_data['programOutcomes']}
        for plo in json_data['programOutcomes']:
            if not all(f in plo for f in ['id', 'description', 'peoAlignment']):
                logger.error(f"PLO missing required fields: {plo.get('id', 'unknown')}")
                return False
            bad_peos = [p for p in plo['peoAlignment'] if p not in valid_peo_ids]
            if bad_peos:
                logger.warning(f"PLO '{plo['id']}' references unknown PEOs: {bad_peos}")

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
    """Convert university syllabus JSON (GA/PEO/PLO/CLO/LLO schema) to formatted Markdown."""
    markdown = f"# {json_data['title']}\n\n"

    if json_data.get('courseCode'):
        markdown += f"**Course Code:** {json_data['courseCode']}\n\n"

    markdown += "## Course Description\n"
    markdown += f"{json_data['courseDescription']}\n\n"

    markdown += "## Course Structure\n"
    markdown += f"**Duration:** {json_data['courseStructure']['duration']}\n"
    markdown += f"**Format:** {json_data['courseStructure']['format']}\n"
    markdown += "\n"

    # Graduate Attributes
    markdown += "## Graduate Attributes\n"
    for section in ['Character', 'Competence', 'Commitment to Service']:
        markdown += f"### {section}\n"
        for item in json_data.get('graduateAttributes', {}).get(section, []):
            markdown += f"- {item}\n"
    markdown += "\n"

    # Program Educational Objectives
    markdown += "## Program Educational Objectives (PEOs) in Relation to Graduate Attributes\n"
    for peo in json_data.get('programEducationalObjectives', []):
        ga_refs = ', '.join(peo.get('graduateAttributeAlignment', []))
        markdown += f"- **{peo['id']}** [{ga_refs}]: {peo['description']}\n"
    markdown += "\n"

    # Programme Learning Outcomes
    markdown += "## Programme Learning Outcomes (PLOs) in Relation to Program Educational Outcomes (PEOs)\n"
    for plo in json_data.get('programOutcomes', []):
        peo_refs = ', '.join(plo.get('peoAlignment', []))
        markdown += f"- **{plo['id']}** [{peo_refs}]: {plo['description']}\n"
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
            "courseCode": json_data.get('courseCode'),
            "description": json_data['courseDescription'],
            "structure": json_data['courseStructure'],
            "graduateAttributes": json_data.get('graduateAttributes', {}),
            "programEducationalObjectives": json_data.get('programEducationalObjectives', []),
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
    logger.info(
        f'Generating syllabus for course: "{prompt_data.get("courseCode", "")}" '
        f'"{prompt_data.get("courseTitle", "")[:50]}..."'
    )
    
    try:
        client = init_gemini()
        
        # Generate structured prompt
        course_title = prompt_data.get('courseTitle', 'Untitled Course')
        course_code = prompt_data.get('courseCode', 'TBD-000')
        duration_weeks = int(prompt_data.get('durationWeeks', 18) or 18)
        lecture_hours = int(prompt_data.get('lectureHours', 3) or 3)
        lab_hours = int(prompt_data.get('labHours', 2) or 2)
        topic_context = prompt_data.get('topic', '').strip()
        graduate_attributes_input = prompt_data.get('graduateAttributesInput', '').strip()
        peos_input = prompt_data.get('peosInput', '').strip()
        plos_input = prompt_data.get('plosInput', '').strip()

        full_prompt = generate_syllabus_prompt(
            course_title,
            course_code,
            duration_weeks,
            lecture_hours,
            lab_hours,
            topic_context,
            graduate_attributes_input,
            peos_input,
            plos_input
        )
        
        model_id = "gemini-3.1-flash-lite-preview"
        
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
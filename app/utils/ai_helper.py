from google import genai
from google.genai.types import GenerateContentConfig, Part
from flask import current_app
import logging
import json
from datetime import datetime
import re
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

def normalize_manual_alignment_data(prompt_data):
    """Normalize structured GA/PEO/PLO input from the frontend alignment editors."""
    ga_input = prompt_data.get('graduateAttributesInput')
    peos_input = prompt_data.get('peosInput')
    plos_input = prompt_data.get('plosInput')

    if not isinstance(ga_input, dict):
        ga_input = {}
    if not isinstance(peos_input, list):
        peos_input = []
    if not isinstance(plos_input, list):
        plos_input = []

    ga_sections = {
        'Character': [],
        'Competence': [],
        'Commitment to Service': []
    }
    ga_id_to_section = {}

    for item in ga_input.get('items', []):
        if not isinstance(item, dict):
            continue
        section = item.get('section')
        ga_id = str(item.get('id', '')).strip()
        description = str(item.get('description', '')).strip()

        if section in ga_sections and description:
            ga_sections[section].append(description)
        if section in ga_sections and ga_id:
            ga_id_to_section[ga_id] = section

    if not any(ga_sections.values()):
        fallback_sections = ga_input.get('sections', {})
        if isinstance(fallback_sections, dict):
            for section in ga_sections:
                values = fallback_sections.get(section, [])
                if isinstance(values, list):
                    ga_sections[section] = [str(v).strip() for v in values if str(v).strip()]

    normalized_peos = []
    for idx, peo in enumerate(peos_input, start=1):
        if not isinstance(peo, dict):
            continue
        peo_id = str(peo.get('id', f'PEO-{idx}')).strip() or f'PEO-{idx}'
        description = str(peo.get('description', '')).strip()
        aligned_ga_ids = peo.get('graduateAttributeAlignment', [])
        if not isinstance(aligned_ga_ids, list):
            aligned_ga_ids = []

        aligned_sections = []
        for ga_id in aligned_ga_ids:
            section = ga_id_to_section.get(str(ga_id).strip())
            if section and section not in aligned_sections:
                aligned_sections.append(section)

        if description:
            normalized_peos.append({
                'id': peo_id,
                'description': description,
                'graduateAttributeAlignment': aligned_sections
            })

    valid_peo_ids = {peo['id'] for peo in normalized_peos}
    normalized_plos = []
    for idx, plo in enumerate(plos_input, start=1):
        if not isinstance(plo, dict):
            continue
        plo_id = str(plo.get('id', f'PLO-{idx}')).strip() or f'PLO-{idx}'
        description = str(plo.get('description', '')).strip()
        peo_alignment = plo.get('peoAlignment', [])
        if not isinstance(peo_alignment, list):
            peo_alignment = []

        filtered_alignment = [
            str(peo_id).strip()
            for peo_id in peo_alignment
            if str(peo_id).strip() in valid_peo_ids
        ]

        if description:
            normalized_plos.append({
                'id': plo_id,
                'description': description,
                'peoAlignment': filtered_alignment
            })

    manual_data = {
        'graduateAttributes': ga_sections,
        'programEducationalObjectives': normalized_peos,
        'programOutcomes': normalized_plos
    }

    return manual_data

def build_fixed_timeframe(duration_weeks, lecture_hours, lab_hours):
    """Build deterministic timeframe fields from user inputs."""
    return {
        'courseStructure': {
            'duration': f'{duration_weeks} weeks',
            'format': f'{lecture_hours}-hour lecture + {lab_hours}-hour laboratory per week'
        },
        'timeFramePerWeek': {
            'lectureHours': lecture_hours,
            'laboratoryHours': lab_hours
        }
    }

def generate_syllabus_prompt(
    course_title,
    course_code,
    duration_weeks,
    lecture_hours,
    lab_hours,
    prelim_exam_week,
    midterm_exam_week,
    final_exam_week,
    topic_context,
    manual_alignment_json
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
6. courseLearningOutcomes (CLOs): exactly 5 items (CLO-1 through CLO-5).
   - Each CLO must have a "ploAlignment" array referencing 1–3 of the PLO ids.
    - CLO descriptions must be specific to '{topic_context or course_title}' and use Bloom's taxonomy verbs.
7. weeklyTopics: cover exactly {duration_weeks} weeks total using weekRange spans (e.g. "1", "1-2", "3-4").
    - Each entry has 2–4 subtopics.
    - Each entry has a "cloAlignment" array referencing 1–3 CLO ids.
        - Each entry has "learningOutcomesASK" as an array of exactly 3 statements only.
        - Use exactly one statement for each domain tag in this exact order:
            1) first statement ends with "(A)"
            2) second statement ends with "(S)"
            3) third statement ends with "(K)"
        - Do not repeat or duplicate A/S/K tags within the same weekly entry.
        - Include dedicated examination weeks using these exact week numbers:
            * Week {prelim_exam_week}: PRELIM EXAMINATION
            * Week {midterm_exam_week}: MIDTERM EXAMINATION
            * Week {final_exam_week}: FINAL EXAMINATION
        - For each examination week, generate appropriate learningOutcomesASK, learningActivities, assessmentStrategies, and resultEvidence for the exam context.
    - The LLO-CLO Alignment Matrix must use learningOutcomesASK statements as row source and entry.cloAlignment as the CLO mapping.
    - Do not create separate LLO objects for matrix mapping.
    - learningActivities: 2–4 specific activities.
    - assessmentStrategies: 2–4 specific tools or methods.
    - resultEvidence: 1–3 concrete evidence items (e.g., "Graded rubric scores").

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
            "learningOutcomesASK": [
                "Learners value collaborative practice and discipline in lab work. (A)",
                "Learners apply foundational procedures in guided tasks. (S)",
                "Learners explain the basic concepts of {topic_context or course_title}. (K)"
            ],
      "subtopics": [
                "History and context of {topic_context or course_title}",
        "Core terminology and conceptual framework",
        "Tools and environment setup"
      ],
      "cloAlignment": ["CLO-1"],
            "kpi": "Identify and explain the foundational concepts and historical context of {topic_context or course_title}.",
      "learningActivities": [
        "Lecture with contextualised slide deck",
        "Think-pair-share discussion on real-world relevance",
        "Lab: Environment setup and guided exploration"
      ],
      "assessmentStrategies": [
        "Terminology quiz (MCQ)",
        "Lab completion checklist and reflection note"
            ],
            "resultEvidence": [
                "Graded quiz results",
                "Graded rubric scores"
      ]
    }}
  ]
}}

USER-PROVIDED CONTENT (USE THIS INSTEAD OF GENERATING NEW GA/PEO/PLO CONTENT)
{manual_alignment_json}

VERIFICATION CHECKLIST — confirm before outputting:
1. JSON is syntactically valid (no trailing commas, no comments).
2. weeklyTopics spans exactly {duration_weeks} weeks.
2.1 Include examination entries at weeks {prelim_exam_week}, {midterm_exam_week}, and {final_exam_week}.
3. Every PEO has graduateAttributeAlignment with valid Graduate Attribute section names.
4. Every PLO has peoAlignment referencing existing PEO ids.
5. Every CLO has ploAlignment referencing existing PLO ids.
6. Every weekly learningOutcomesASK entry maps to existing CLO ids through entry.cloAlignment.
7. Every weeklyTopic entry has cloAlignment referencing existing CLO ids.
8. All required fields present in every object."""

    return prompt

def validate_json_structure(json_data):
    """Validate the JSON structure matches the university syllabus schema with GA/PEO/PLO/CLO/LLO."""
    required_top = ['title', 'courseDescription', 'courseStructure',
                    'graduateAttributes', 'programEducationalObjectives',
                    'programOutcomes', 'courseLearningOutcomes', 'weeklyTopics']
    course_structure_fields = ['duration', 'format']
    weekly_topic_fields = ['weekRange', 'mainTopic', 'learningOutcomesASK', 'subtopics', 'cloAlignment',
                           'learningActivities', 'assessmentStrategies', 'resultEvidence']

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

            outcomes = entry['learningOutcomesASK']
            if not isinstance(outcomes, list) or len(outcomes) != 3:
                logger.error(f"Entry Week {wr}: learningOutcomesASK must contain exactly 3 items (A, S, K)")
                return False

            tags = []
            for outcome in outcomes:
                if not isinstance(outcome, str):
                    logger.error(f"Entry Week {wr}: each learningOutcomesASK item must be a string")
                    return False
                match = re.search(r'\(([ASK])\)\s*$', outcome.strip())
                if not match:
                    logger.error(f"Entry Week {wr}: learning outcome must end with (A), (S), or (K)")
                    return False
                tags.append(match.group(1))

            if tags != ['A', 'S', 'K']:
                logger.error(f"Entry Week {wr}: learningOutcomesASK must be in exact order (A), (S), (K)")
                return False

            if not isinstance(entry['learningActivities'], list) or len(entry['learningActivities']) < 1:
                logger.error(f"Entry Week {wr}: learningActivities must be a non-empty list")
                return False

            if not isinstance(entry['assessmentStrategies'], list) or len(entry['assessmentStrategies']) < 1:
                logger.error(f"Entry Week {wr}: assessmentStrategies must be a non-empty list")
                return False

            if not isinstance(entry['resultEvidence'], list) or len(entry['resultEvidence']) < 1:
                logger.error(f"Entry Week {wr}: resultEvidence must be a non-empty list")
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
    markdown += "| Week | Learning Outcome (A,S,K) | Topic | Time Frame | Learning Activity / Performance Task | Assessment Strategy and Tool | Result & Evidence |\n"
    markdown += "|------|--------------------------|-------|------------|--------------------------------------|------------------------------|------------------|\n"
    for entry in json_data['weeklyTopics']:
        learning_outcomes = '<br>'.join(f"- {s}" for s in entry.get('learningOutcomesASK', []))
        subtopics = '<br>'.join(f"- {s}" for s in entry['subtopics'])
        topic = f"**{entry['mainTopic']}**<br>{subtopics}"
        timeframe = (
            f"- {json_data.get('timeFramePerWeek', {}).get('lectureHours', 3)} Hours<br>"
            f"- {json_data.get('timeFramePerWeek', {}).get('laboratoryHours', 2)} Hours"
        )
        activities = '<br>'.join(f"- {a}" for a in entry['learningActivities'])
        strategies = '<br>'.join(f"- {s}" for s in entry.get('assessmentStrategies', []))
        evidence = '<br>'.join(f"- {e}" for e in entry.get('resultEvidence', []))
        markdown += f"| Week {entry['weekRange']} | {learning_outcomes} | {topic} | {timeframe} | {activities} | {strategies} | {evidence} |\n"
    markdown += "\n"

    # LLO-CLO Alignment Matrix (derived from Learning Outcome A/S/K rows)
    if clos:
        clo_ids = [c['id'] for c in clos]
        markdown += "## LLO-CLO Alignment Matrix\n\n"
        header = "| LLO | " + " | ".join(clo_ids) + " |\n"
        sep = "|-----" + "|".join(["------"] * len(clo_ids)) + "|\n"
        markdown += header + sep
        for entry_idx, entry in enumerate(json_data['weeklyTopics'], start=1):
            for outcome_idx, outcome in enumerate(entry.get('learningOutcomesASK', []), start=1):
                aligned = set(entry.get('cloAlignment', []))
                cells = " | ".join("✓" if cid in aligned else "" for cid in clo_ids)
                markdown += f"| LO-{entry_idx}.{outcome_idx}: {outcome} | {cells} |\n"
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
        prelim_exam_week = int(prompt_data.get('prelimExamWeek', 6) or 6)
        midterm_exam_week = int(prompt_data.get('midtermExamWeek', 12) or 12)
        final_exam_week = int(prompt_data.get('finalExamWeek', 18) or 18)
        topic_context = prompt_data.get('topic', '').strip()

        manual_alignment_data = normalize_manual_alignment_data(prompt_data)
        fixed_timeframe = build_fixed_timeframe(duration_weeks, lecture_hours, lab_hours)
        manual_alignment_json = json.dumps(manual_alignment_data, ensure_ascii=True, indent=2)

        full_prompt = generate_syllabus_prompt(
            course_title,
            course_code,
            duration_weeks,
            lecture_hours,
            lab_hours,
            prelim_exam_week,
            midterm_exam_week,
            final_exam_week,
            topic_context,
            manual_alignment_json
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

            # Enforce manual GA/PEO/PLO content from the input editor.
            json_data['graduateAttributes'] = manual_alignment_data['graduateAttributes']
            json_data['programEducationalObjectives'] = manual_alignment_data['programEducationalObjectives']
            json_data['programOutcomes'] = manual_alignment_data['programOutcomes']
            json_data['courseStructure'] = fixed_timeframe['courseStructure']
            json_data['timeFramePerWeek'] = fixed_timeframe['timeFramePerWeek']
            
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
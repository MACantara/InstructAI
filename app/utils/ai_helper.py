from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part
from flask import current_app
import logging
import json

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug logs are captured
logger.propagate = False

def init_gemini():
    """Initialize Gemini client"""
    logger.debug('Initializing Gemini client')
    try:
        client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        logger.info('Gemini client initialized successfully')
        return client
    except Exception as e:
        logger.error(f'Failed to initialize Gemini client: {str(e)}')
        raise

def extract_search_metadata(response_candidate):
    """Extract and structure search metadata from response"""
    metadata = {}
    
    if hasattr(response_candidate, 'grounding_metadata'):
        meta = response_candidate.grounding_metadata
        
        # Extract grounding chunks focusing on web title and URI
        if meta.grounding_chunks:
            metadata['chunks'] = []
            logger.debug('Grounding chunks found:')
            for chunk in meta.grounding_chunks:
                chunk_data = chunk.model_dump()
                if 'web' in chunk_data:
                    web_data = {
                        'title': chunk_data['web'].get('title', 'Unknown title'),
                        'source': chunk_data['web'].get('uri', 'Unknown source')
                    }
                    metadata['chunks'].append(web_data)
                    logger.debug(f"Source: {web_data['title']} - {web_data['source']}")
    
    return metadata

def generate_syllabus_prompt(topic, include_objectives=True, include_readings=True):
    """Generate a structured prompt for syllabus creation"""
    prompt = f"""You are an experienced curriculum designer with expertise in creating comprehensive syllabi. 
Your task is to create a detailed, well-structured syllabus for '{topic}'.

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
    weekly_topic_fields = ['week', 'mainTopic', 'description', 'topics']

    # Check required top-level fields
    if not all(field in json_data for field in required_fields):
        return False

    # Validate course structure
    if not all(field in json_data['courseStructure'] for field in course_structure_fields):
        return False

    # Validate weekly topics
    if not isinstance(json_data['weeklyTopics'], list) or not json_data['weeklyTopics']:
        return False

    for week in json_data['weeklyTopics']:
        if not all(field in week for field in weekly_topic_fields):
            return False

        if not isinstance(week['topics'], list):
            return False

        for topic in week['topics']:
            if not all(field in topic for field in ['subtitle', 'points']):
                return False
            if not isinstance(topic['points'], list):
                return False

    return True

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

def generate_response(prompt_data):
    """Generate response using Gemini with Google Search integration"""
    logger.info(f'Generating syllabus for topic: "{prompt_data["topic"][:50]}..."')
    
    try:
        client = init_gemini()
        
        # Generate structured prompt
        full_prompt = generate_syllabus_prompt(
            prompt_data["topic"],
            prompt_data.get("include_objectives", True),
            prompt_data.get("include_readings", True)
        )
        
        model_id = "gemini-2.0-flash-exp"
        
        logger.debug('Initializing Google Search tool')
        google_search_tool = Tool(
            google_search=GoogleSearch()
        )
        
        logger.debug('Configuring generation parameters')
        config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
            tools=[google_search_tool],
            response_modalities=["TEXT"],
            max_output_tokens=8192,
            stop_sequences=["STOP!"],
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
        
        logger.debug('Sending request to Gemini API')
        response = client.models.generate_content(
            model=model_id,
            contents=Part.from_text(full_prompt),
            config=config
        )
        
        if not response or not response.candidates:
            logger.warning('No response generated from API')
            return {"text": "No response generated", "metadata": {}}
        
        result = response.candidates[0].content.parts[0].text
        
        try:
            # Clean the response to ensure it's valid JSON
            # Remove any leading/trailing non-JSON content
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
        
        metadata = extract_search_metadata(response.candidates[0])
        
        return {
            "text": formatted_text,
            "metadata": metadata,
            "raw_json": json_data if 'json_data' in locals() else None
        }
        
    except Exception as e:
        logger.error(f'Error generating response: {str(e)}', exc_info=True)
        raise
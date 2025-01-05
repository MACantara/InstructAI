from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part
from flask import current_app
import logging
import json

logger = logging.getLogger(__name__)

def generate_weekly_content(topic, week_data):
    """Generate detailed content for a specific weekly topic"""
    prompt = f"""Generate comprehensive course content for Week {week_data['week']}: {week_data['mainTopic']}
    following this JSON structure:

    {{
        "week": {week_data['week']},
        "topic": "{week_data['mainTopic']}",
        "content": {{
            "lecture": {{
                "notes": "Detailed lecture notes in markdown",
                "slides": ["Key points for slides"],
                "examples": ["Code or practical examples"]
            }},
            "resources": {{
                "videos": [
                    {{
                        "title": "Video title",
                        "url": "Video URL",
                        "description": "Brief description"
                    }}
                ],
                "articles": [
                    {{
                        "title": "Article title",
                        "url": "Article URL",
                        "relevance": "Why this is important"
                    }}
                ],
                "tools": [
                    {{
                        "name": "Tool name",
                        "url": "Tool URL",
                        "purpose": "How it's used in this topic"
                    }}
                ]
            }},
            "exercises": [
                {{
                    "title": "Exercise title",
                    "description": "Exercise description",
                    "difficulty": "beginner|intermediate|advanced",
                    "instructions": ["Step-by-step instructions"]
                }}
            ]
        }}
    }}"""

    try:
        client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        config = GenerateContentConfig(
            temperature=0.7,
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
            return json.loads(response.candidates[0].content.parts[0].text)
        
        return None
    except Exception as e:
        logger.error(f"Error generating content for week {week_data['week']}: {str(e)}")
        return None

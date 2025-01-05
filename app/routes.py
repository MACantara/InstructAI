from flask import Blueprint, render_template, request, jsonify, current_app
import traceback
from .utils.ai_helper import generate_response
from .utils.content_generator import generate_weekly_content

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/debug-sentry')
def trigger_error():
    """Route for testing error tracking"""
    division_by_zero = 1 / 0
    return division_by_zero

@main_bp.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        if not data or 'topic' not in data:
            return jsonify({'error': 'No topic provided'}), 400
        
        current_app.logger.info(f'Generating syllabus for topic: {data["topic"]}')
        response = generate_response(data)
        return jsonify({'response': response})
    
    except Exception as e:
        current_app.logger.error(f'Error generating response: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@main_bp.route('/generate/week-content', methods=['POST'])
def generate_week_content():
    """Generate detailed content for a specific week"""
    try:
        data = request.json
        if not data or 'weekData' not in data:
            return jsonify({'error': 'No week data provided'}), 400

        current_app.logger.info(f'Generating content for week {data["weekData"].get("week", "unknown")}')
        
        # Generate detailed content for the week
        content = generate_weekly_content(
            topic=data['weekData'].get('mainTopic', ''),
            week_data=data['weekData']
        )
        
        if content is None:
            return jsonify({'error': 'Failed to generate weekly content'}), 500
            
        return jsonify({
            'content': content,
            'week': data['weekData'].get('week')
        })
        
    except Exception as e:
        current_app.logger.error(f'Error generating weekly content: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
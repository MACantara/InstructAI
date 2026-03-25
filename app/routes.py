from flask import Blueprint, render_template, request, jsonify, current_app
from markupsafe import Markup
import traceback
from .utils.ai_helper import generate_response

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
        if not data or 'courseTitle' not in data or 'courseCode' not in data:
            return jsonify({'error': 'Course title and course code are required'}), 400
        
        current_app.logger.info(
            f'Generating syllabus for course: {data["courseCode"]} - {data["courseTitle"]}'
        )
        response = generate_response(data)
        return jsonify({'response': response})
    
    except Exception as e:
        current_app.logger.error(f'Error generating response: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

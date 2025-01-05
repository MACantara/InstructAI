from flask import Blueprint, render_template, request, jsonify, current_app
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
        prompt = request.json.get('prompt')
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        current_app.logger.info(f'Generating response for prompt: {prompt}')
        response = generate_response(prompt)
        return jsonify({'response': response})
    
    except Exception as e:
        current_app.logger.error(f'Error generating response: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
from flask import Blueprint, render_template, request, jsonify
from .utils.ai_helper import generate_response

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/generate', methods=['POST'])
def generate():
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    response = generate_response(prompt)
    return jsonify({'response': response})
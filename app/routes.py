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
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if 'weekData' not in data:
            return jsonify({'error': 'No week data provided'}), 400

        if 'courseId' not in data:
            return jsonify({'error': 'Course ID is required'}), 400

        week_data = data['weekData']
        course_id = data.get('courseId')

        try:
            course_id = int(course_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid course ID format'}), 400

        if not isinstance(week_data, dict):
            return jsonify({'error': 'Invalid week data format'}), 400

        current_app.logger.info(f'Generating content for week {week_data.get("week", "unknown")} of course {course_id}')
        
        content = generate_weekly_content(
            topic=week_data.get('mainTopic', ''),
            week_data=week_data,
            course_id=course_id
        )
        
        if content is None:
            return jsonify({
                'error': 'Failed to generate weekly content',
                'week': week_data.get('week')
            }), 500
            
        return jsonify({
            'content': content,
            'week': week_data.get('week'),
            'course_id': course_id
        })
        
    except Exception as e:
        current_app.logger.error(f'Error generating weekly content: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'details': traceback.format_exc()
        }), 500

@main_bp.route('/week-content/<int:week_number>')
def view_week_content(week_number):
    try:
        content = request.args.get('content', '')
        topic = request.args.get('topic', '')
        return render_template('week_content.html', 
                             week_number=week_number,
                             topic=topic,
                             content=content)
    except Exception as e:
        current_app.logger.error(f'Error displaying week content: {str(e)}')
        return jsonify({'error': 'Failed to display content'}), 500
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables"""
    load_dotenv()
    
    # Get database connection details from environment variables
    db_url = os.getenv('POSTGRES_URL_NON_POOLING')
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create tables
        create_tables = """
        -- Courses table
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            structure JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Weekly topics table
        CREATE TABLE IF NOT EXISTS weekly_topics (
            id SERIAL PRIMARY KEY,
            course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
            week_number INTEGER NOT NULL,
            main_topic VARCHAR(255) NOT NULL,
            description TEXT,
            content JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(course_id, week_number)
        );

        -- Resources table (for videos, articles, tools)
        CREATE TABLE IF NOT EXISTS resources (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            type VARCHAR(50) NOT NULL, -- 'video', 'article', or 'tool'
            title VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Activities table
        CREATE TABLE IF NOT EXISTS activities (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            duration VARCHAR(50),
            type VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Assignments table
        CREATE TABLE IF NOT EXISTS assignments (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            due_date VARCHAR(100),
            weightage VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Quizzes table
        CREATE TABLE IF NOT EXISTS quizzes (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            format VARCHAR(100),
            duration VARCHAR(50),
            num_questions INTEGER,
            total_points INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Update trigger for courses
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Create triggers for updating timestamps
        DROP TRIGGER IF EXISTS update_courses_updated_at ON courses;
        CREATE TRIGGER update_courses_updated_at
            BEFORE UPDATE ON courses
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_weekly_topics_updated_at ON weekly_topics;
        CREATE TRIGGER update_weekly_topics_updated_at
            BEFORE UPDATE ON weekly_topics
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        # Execute table creation
        cur.execute(create_tables)
        logger.info("Successfully created database tables")
        
        # Create indexes for better performance
        indexes = """
        CREATE INDEX IF NOT EXISTS idx_weekly_topics_course_id ON weekly_topics(course_id);
        CREATE INDEX IF NOT EXISTS idx_resources_weekly_topic_id ON resources(weekly_topic_id);
        CREATE INDEX IF NOT EXISTS idx_activities_weekly_topic_id ON activities(weekly_topic_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_weekly_topic_id ON assignments(weekly_topic_id);
        CREATE INDEX IF NOT EXISTS idx_quizzes_weekly_topic_id ON quizzes(weekly_topic_id);
        """
        
        cur.execute(indexes)
        logger.info("Successfully created indexes")
        
        # Add new tables for additional content
        additional_tables = """
        -- Key Points table
        CREATE TABLE IF NOT EXISTS key_points (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Examples table
        CREATE TABLE IF NOT EXISTS examples (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            title TEXT,
            content TEXT NOT NULL,
            code_snippet TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Practice Exercises table
        CREATE TABLE IF NOT EXISTS practice_exercises (
            id SERIAL PRIMARY KEY,
            weekly_topic_id INTEGER REFERENCES weekly_topics(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            difficulty VARCHAR(50),
            instructions JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Additional indexes
        CREATE INDEX IF NOT EXISTS idx_key_points_weekly_topic_id ON key_points(weekly_topic_id);
        CREATE INDEX IF NOT EXISTS idx_examples_weekly_topic_id ON examples(weekly_topic_id);
        CREATE INDEX IF NOT EXISTS idx_practice_exercises_weekly_topic_id ON practice_exercises(weekly_topic_id);
        """
        
        # Execute additional tables creation
        cur.execute(additional_tables)
        logger.info("Successfully created additional content tables")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db()

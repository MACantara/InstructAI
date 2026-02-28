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

        -- Weekly topics table (keeping for syllabus structure if needed, but removing content-specific tables)
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
        """
        
        cur.execute(indexes)
        logger.info("Successfully created indexes")
        
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

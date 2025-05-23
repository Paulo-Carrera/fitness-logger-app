import os
from dotenv import load_dotenv
import urllib.parse
import json

from models import Exercise, db
from app import app

# Load environment variables
load_dotenv()

# Read from .env
db_user = os.getenv('DB_USER')
db_password = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))  # URL-encode special characters
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

# Build connection string
manual_db_url = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
os.environ['DATABASE_URL'] = manual_db_url

# print("Using DATABASE_URL:", os.getenv('DATABASE_URL'))

def seed_exercises():
    json_path = os.path.join(os.path.dirname(__file__), 'static/data/exercises.json')
    with app.app_context():
        try:
            with open(json_path) as f:
                exercises = json.load(f)

            for exercise in exercises:
                ex = Exercise(id=exercise['id'], name=exercise['name'], description=exercise.get('description'))
                db.session.merge(ex)

            db.session.commit()
            print("✅ Seeded exercises into the database.")
        except Exception as e:
            print(f"❌ Error seeding exercises: {e}")

if __name__ == '__main__':
    seed_exercises()


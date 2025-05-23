import os
from dotenv import load_dotenv
import json

from models import Exercise, db
from app import app

# Load environment variables
load_dotenv()

def seed_exercises():
    json_path = os.path.join(os.path.dirname(__file__), 'static/data/exercises.json')
    with app.app_context():
        try:
            with open(json_path) as f:
                exercises = json.load(f)

            for exercise in exercises:
                ex = Exercise(
                    id=exercise['id'],
                    name=exercise['name'],
                    description=exercise.get('description')
                )
                db.session.merge(ex)

            db.session.commit()
            print("✅ Seeded exercises into the database.")
        except Exception as e:
            print(f"❌ Error seeding exercises: {e}")

if __name__ == '__main__':
    seed_exercises()

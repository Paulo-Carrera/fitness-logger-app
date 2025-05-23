import json 
import os 

def get_exercises():
    """Load exercises from local JSON file."""
    json_path = os.path.join(os.path.dirname(__file__), "static", "data", "exercises.json")
    with open(json_path) as f:
        print(f)
        return json.load(f)
    return exercises 
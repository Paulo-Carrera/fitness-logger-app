import os
import pytz
from dotenv import load_dotenv
load_dotenv()
# print(os.getenv('DATABASE_URL'))

from flask import Flask, jsonify, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from functools import wraps
from datetime import datetime, timedelta, timezone
from models import db, User, Workout, WorkoutExercise, Exercise
from flask_migrate import Migrate
from api_client import get_exercises

# Flask setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')
app.debug = True 
app.config['DEBUG'] = True

# DB and migration
db.init_app(app)
migrate = Migrate(app, db)

# Login required decorator
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped_view

def update_streak(user):
    today = datetime.utcnow().date()

    # Get all unique workout dates for the user, sorted descending
    workout_dates = (
        db.session.query(db.func.date(Workout.date))
        .filter_by(user_id=user.id)
        .distinct()
        .order_by(db.func.date(Workout.date).desc())
        .all()
    )

    workout_dates = [d[0] for d in workout_dates]  # unpack date tuples

    if not workout_dates:
        user.streak_count = 0
        user.last_logged_date = None
    else:
        # Recalculate streak from today going backwards
        streak = 0
        expected_day = today

        for d in workout_dates:
            if d == expected_day:
                streak += 1
                expected_day -= timedelta(days=1)
            elif d < expected_day:
                break  # streak is broken
            else:
                continue  # future dates (shouldn’t happen)

        user.streak_count = streak
        user.last_logged_date = workout_dates[0]

    db.session.commit()


# Home
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Timezone
@app.route('/set-timezone', methods=['POST'])
@login_required
def set_timezone():
    tz = request.form.get('timezone')
    if tz in pytz.all_timezones:
        session['timezone'] = tz
        flash(f'Timezone set to {tz}', 'info')
    else:
        flash('Invalid timezone selected', 'warning')
    return redirect(url_for('dashboard'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])

    # Eager load Workout.exercises and each WorkoutExercise.exercise
    workouts = Workout.query.options(
        joinedload(Workout.exercises).joinedload(WorkoutExercise.exercise)
    ).filter_by(user_id=user.id).order_by(Workout.date.desc()).all()

    # Debug print to verify cardio data
    for workout in workouts:
        for we in workout.exercises:
            print(f"{we.exercise.name} | is_cardio: {we.exercise.is_cardio} | duration: {we.duration}")

    timezones = pytz.all_timezones
    update_streak(user)

    return render_template('dashboard.html', user=user, workouts=workouts, timezones=timezones)

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash('Registration Successful!')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        session['timezone'] = 'US/Arizona'

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login Successful!')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout Successful!')
    return redirect(url_for('login'))

# Return JSON list of exercises (from your API client or DB)
@app.route('/exercises')
def exercises():
    # You might want to load from DB instead of your api_client
    exercises = Exercise.query.all()
    simplified = [{'id': ex.id, 'name': ex.name, 'description': ex.description} for ex in exercises]
    return jsonify(simplified)

# Create workout with exercises
@app.route("/create-workout", methods=["GET", "POST"])
@login_required
def create_workout():
    exercises = get_exercises()  # Loads from JSON or DB

    if request.method == "POST":
        workout_name = request.form.get("name", "My Workout")
        selected_ids = request.form.getlist("selected_exercises")  # List of selected checkbox values

        if not selected_ids:
            flash("Please select at least one exercise to create a workout.", "warning")
            return redirect(url_for("create_workout"))

        # 1. Create new workout for the user
        workout = Workout(name=workout_name, user_id=session["user_id"])
        db.session.add(workout)
        db.session.flush()  # Get workout.id before commit

        # 2. Attach selected exercises
        for ex_id in selected_ids:
            exercise = Exercise.query.get(int(ex_id))

            if not exercise:
                continue  # Skip invalid IDs just in case

            if exercise.is_cardio:
                # Handle cardio duration input
                duration = request.form.get(f"duration_{ex_id}")
                try:
                    duration = int(duration)
                except (TypeError, ValueError):
                    duration = 10  # Default if not provided or invalid

                workout_exercise = WorkoutExercise(
                    workout_id=workout.id,
                    exercise_id=exercise.id,
                    duration=duration
                )
            else:
                # Handle strength sets and reps input
                sets = request.form.get(f"sets_{ex_id}")
                reps = request.form.get(f"reps_{ex_id}")
                try:
                    sets = int(sets)
                except (TypeError, ValueError):
                    sets = 3
                try:
                    reps = int(reps)
                except (TypeError, ValueError):
                    reps = 10

                workout_exercise = WorkoutExercise(
                    workout_id=workout.id,
                    exercise_id=exercise.id,
                    sets=sets,
                    reps=reps
                )

            db.session.add(workout_exercise)

        # 3. Save to DB
        db.session.commit()

        flash("Workout created successfully!")
        return redirect(url_for("dashboard"))

    return render_template("create_workout.html", exercises=exercises)


@app.route("/workout_exercise/<int:we_id>/update", methods=["POST"])
@login_required
def update_workout_exercise(we_id):
    we = WorkoutExercise.query.get_or_404(we_id)

    if we.exercise.is_cardio:
        we.duration = request.form.get("duration", type=int)
    else:
        we.sets = request.form.get("sets", type=int)
        we.reps = request.form.get("reps", type=int)

    db.session.commit()
    flash("Workout exercise updated.", "success")
    return redirect(url_for("dashboard"))

# Delete workout
@app.route('/delete-workout/<int:workout_id>', methods=['POST'])
@login_required
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)

    if workout.user_id != session['user_id']:
        flash("You do not have permission to delete this workout!")
        return redirect(url_for('dashboard'))

    # Delete associated WorkoutExercise records
    WorkoutExercise.query.filter_by(workout_id=workout_id).delete()
    # Delete the workout itself
    db.session.delete(workout)
    db.session.commit()

    # Recalculate and update user's streak after deletion
    user = User.query.get(session['user_id'])
    update_streak(user)

    flash('Workout deleted successfully!')
    return redirect(url_for('dashboard'))

@app.template_filter('convert_timezone')
def convert_timezone_filter(value, timezone='UTC'):
    if value is None:
        return ""
    if not isinstance(value, datetime):
        return value
    try:
        utc = pytz.utc.localize(value) if value.tzinfo is None else value.astimezone(pytz.utc)
        target_tz = pytz.timezone(timezone)
        return utc.astimezone(target_tz).strftime('%Y-%m-%d %I:%M %p')
    except Exception as e:
        return value  # Fallback

# Run app
if __name__ == '__main__':
    app.run(debug=True)
 
import os
import traceback
from flask import Flask, render_template, request, session, jsonify
from owlready2 import get_ontology
import random


class MathLearningPlatform:
    def __init__(self, ontology_path):
        try:
            # Normalize the ontology path
            normalized_path = os.path.abspath(ontology_path)
            if not os.path.exists(normalized_path):
                raise FileNotFoundError(f"Ontology file not found: {normalized_path}")

            # Use correct URI for loading ontology
            file_uri = f"file://{normalized_path.replace(os.path.sep, '/')}"
            self.onto = get_ontology(file_uri).load()

            # List of problem types and difficulties
            self.problem_types = ["Algebra", "Geometry"]
            self.difficulties = ["Easy", "Medium", "Hard"]

        except Exception as e:
            print(f"Error initializing application: {e}")
            print(traceback.format_exc())
            raise

    def register_student(self, name, grade):
        """Register a student and return their details."""
        return {
            "name": name,
            "grade": grade,
            "problems_solved": []
        }

    def generate_problem(self, problem_type, difficulty):
        """Generate a math problem based on type and difficulty."""
        try:
            problems = [
                problem
                for problem in self.onto.Problem.instances()
                if problem_type in problem.is_a[0].name and difficulty in problem.hasLevel[0]
            ]

            if problems:
                problem = random.choice(problems)
                return {
                    "question": problem.hasQuestion[0],
                    "correct_answer": problem.hasAnswer[0],
                    "problem_type": problem_type,
                    "difficulty": difficulty
                }
            else:
                return None
        except Exception as e:
            print(f"Error generating problem: {e}")
            return None

# Flask Application Setup
app = Flask(__name__)
app.secret_key = 'math_learning_platform_secret_key'

# Initialize the Math Learning Platform
try:
    ontology_path = r"D:\\TRIMPLIN_STATS\\protege files\\math_tutor_project\\Math Learning Platform\\math_tutoring_ontology.owl"
    math_platform = MathLearningPlatform(ontology_path)
except Exception as e:
    print(f"Failed to initialize Math Learning Platform: {e}")
    math_platform = None

@app.route('/')
def index():
    return render_template('index.html', 
                           problem_types=math_platform.problem_types, 
                           difficulties=math_platform.difficulties)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    grade = request.form.get('grade')

    if not name or not grade:
        return jsonify({"error": "Please enter name and select grade"}), 400

    student = math_platform.register_student(name, grade)
    session['student'] = student
    return jsonify({
        "message": f"Student {name} registered successfully",
        "name": name,
        "grade": grade
    })

@app.route('/generate_problem', methods=['POST'])
def generate_problem():
    if 'student' not in session:
        return jsonify({"error": "Please register a student first"}), 401

    problem_type = request.form.get('problem_type')
    difficulty = request.form.get('difficulty')

    if not problem_type or not difficulty:
        return jsonify({"error": "Please select problem type and difficulty"}), 400

    problem = math_platform.generate_problem(problem_type, difficulty)
    
    if problem:
        session['current_problem'] = problem
        return jsonify(problem)
    else:
        return jsonify({"error": "No problem found for the selected criteria"}), 404

@app.route('/check_answer', methods=['POST'])
def check_answer():
    if 'student' not in session or 'current_problem' not in session:
        return jsonify({"error": "No active problem"}), 401

    user_answer = request.form.get('answer')
    current_problem = session['current_problem']
    student = session['student']

    result = "Correct" if user_answer.strip() == current_problem['correct_answer'].strip() else "Incorrect"

    # Update student's problem solving record
    student_record = {
        "question": current_problem['question'],
        "problem_type": current_problem['problem_type'],
        "difficulty": current_problem['difficulty'],
        "result": result
    }
    student['problems_solved'].append(student_record)
    session['student'] = student

    return jsonify({
        "result": result,
        "correct_answer": current_problem['correct_answer'] if result == "Incorrect" else None,
        "problems_solved": student['problems_solved']
    })

if __name__ == '__main__':
    app.run(debug=True)
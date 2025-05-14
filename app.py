import pickle
import os
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import requests
from dotenv import load_dotenv
load_dotenv()
import sys
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = os.getenv("API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent"


# Flask App Setup
app = Flask(__name__)
app.secret_key = 'your_secure_random_secret_key'

# MongoDB Setup
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["faculty_portal"]
users_collection = db["users"]

# Ensure the model file exists
model_path = "faculty_prediction_model.pkl"

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file '{model_path}' not found. Place it in the models directory.")

# Load trained model
with open(model_path, "rb") as model_file:
    model = pickle.load(model_file)

# Define expected input features
FEATURES = [
    "Years of Service", "Patent Count", "Publication Records (Journals)",
    "Publication Records (Conferences)", "Student Engagement (1-10)",
    "Doubt Resolution (1-10)", "Teaching Innovation Metrics (1-10)",
    "Student Success Rates (1-10)"
]

# Mapping predictions to actual designations
designation_mapping = {
    0: "Junior Lecturer",
    1: "Assistant Professor",
    2: "Associate Professor",
    3: "Lecturer",
    4: "Senior Lecturer",
    5: "Professor"
}

def generate_recommendations(user_data):
    recommendations = []

    # Research & Publications
    if user_data["Publication Records (Journals)"] < 3:
        recommendations.append(("Writing in the Sciences", "https://www.coursera.org/learn/sciwrite"))

    if user_data["Publication Records (Conferences)"] < 3:
        recommendations.append(("Academic Writing", "https://www.udemy.com/course/nbeacademicwriting"))

    # Patent & Innovation
    if user_data["Patent Count"] <= 2:
        recommendations.append(("Intellectual Property Law and Policy", "https://www.udemy.com/course/basics-of-intellectual-property-rights"))

    if user_data["Patent Count"] <= 2:
        recommendations.append(("Patent Law Essentials", "https://www.coursera.org/learn/patents"))

    # Teaching & Student Engagement
    if user_data["Student Engagement (1-10)"] < 7:
        recommendations.append(("Advanced Instructional Strategies in the Virtual Classroom", "https://www.coursera.org/learn/teaching-strategies"))

    if user_data["Student Engagement (1-10)"] < 7:
        recommendations.append(("Engaging Students for Deeper Learning", "https://teachingcommons.stanford.edu/teaching-guides/foundations-course-design/learning-activities/increasing-student-engagement"))

    if user_data["Doubt Resolution (1-10)"] < 7:
        recommendations.append(("Effective Mentoring", "https://onlinecourses.swayam2.ac.in/ntr24_ed60/preview"))

    if user_data["Teaching Innovation Metrics (1-10)"] < 7:
        recommendations.append(("Giving Effective Feedback", "https://www.udemy.com/course/giving-and-receiving-effective-feedback/"))

    # Leadership & Career Growth
    if user_data["Student Success Rates (1-10)"] < 7:
        recommendations.append(("Educational Leadership and Management", "https://onlinecourses.nptel.ac.in/noc22_hs109/preview"))

    return recommendations



# Flask Forms for Authentication and Prediction
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class FacultyForm(FlaskForm):
    years_of_service = IntegerField("Years of Service", validators=[DataRequired()])
    patent_count = IntegerField("Patent Count", validators=[DataRequired()])
    publication_count = IntegerField("Publication Records (Journals)", validators=[DataRequired()])
    conference_count = IntegerField("Publication Records (Conferences)", validators=[DataRequired()])
    student_engagement = IntegerField("Student Engagement (1-10)", validators=[DataRequired()])
    doubt_resolution = IntegerField("Doubt Resolution (1-10)", validators=[DataRequired()])
    teaching_innovation = IntegerField("Teaching Innovation Metrics (1-10)", validators=[DataRequired()])
    student_success = IntegerField("Student Success Rates (1-10)", validators=[DataRequired()])
    submit = SubmitField("Predict")

# Home Page Route
@app.route('/')
def home():
    return render_template('home.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = users_collection.find_one({"username": form.username.data})
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(form.password.data)
        users_collection.insert_one({"username": form.username.data, "password": hashed_password})
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users_collection.find_one({"username": form.username.data})
        if user and check_password_hash(user["password"], form.password.data):
            session["username"] = user["username"]
            flash("Login successful!", "success")
            return redirect(url_for('teacher_dashboard'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('login.html', form=form)

# Logout Route
@app.route('/logout')
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# Faculty Dashboard Route
@app.route('/teacher', methods=['GET', 'POST'])
def teacher_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    form = FacultyForm()
    prediction = None

    if form.validate_on_submit():
        print("✅ Form Submitted Successfully!")  # Debugging Log
        user_data = {
            "Years of Service": form.years_of_service.data,
            "Patent Count": form.patent_count.data,
            "Publication Records (Journals)": form.publication_count.data,
            "Publication Records (Conferences)": form.conference_count.data,
            "Student Engagement (1-10)": form.student_engagement.data,
            "Doubt Resolution (1-10)": form.doubt_resolution.data,
            "Teaching Innovation Metrics (1-10)": form.teaching_innovation.data,
            "Student Success Rates (1-10)": form.student_success.data
        }


        input_df = pd.DataFrame([user_data])
        input_df = input_df.reindex(columns=FEATURES, fill_value=0)
        print(input_df)
        try:
            prediction_index = model.predict(input_df)[0]
            prediction = designation_mapping.get(prediction_index, "Unknown Designation")
            print(prediction)
            session['recommendations'] = generate_recommendations(user_data)
        except Exception as e:
            flash(f"Prediction error: {str(e)}", "danger")
    else:
        print(form.errors)

    return render_template('teacher_dashboard.html', form=form, prediction=prediction)


@app.route('/recommendations')
def recommendations():
    if 'username' not in session or 'recommendations' not in session:
        return redirect(url_for('login'))
    return render_template('recommendations.html', recommendations=session['recommendations'])
# Resources Page Route
@app.route('/resources')
def resources():
    return render_template('resources.html')

import requests
import os

API_KEY = os.getenv("API_KEY")  # Get API key from environment variable
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"

import re

def format_review_as_html(review_text, title="Research Paper Review"):
    """Converts the review text to HTML-friendly format, adapted for Gemini-generated reviews,
    removing the initial heading if present and adding a custom title."""

    # Remove the initial heading if present
    if review_text.startswith("## "):
        review_text = review_text.split('\n\n', 1)[1] if '\n\n' in review_text else review_text

    # Handle potential bullet points or numbered lists (common in Gemini output)
    review_text = re.sub(r"^\s*-\s*(.*?)$", r"<li>\1</li>", review_text, flags=re.MULTILINE)
    review_text = re.sub(r"^\s*\d+\.\s*(.*?)$", r"<li>\1</li>", review_text, flags=re.MULTILINE)

    # Paragraphs
    review_text = review_text.replace("\n\n", "</p><p>")

    # Line breaks
    review_text = review_text.replace("\n", "<br>")

    # Bold text
    review_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", review_text)

    # Italic text
    review_text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", review_text)

    # Handle lists
    if "<li>" in review_text:
        if review_text.startswith("<li>"):
            review_text = f"<ul>{review_text}</ul>"
        else:
            review_text = review_text.replace("<li>", "<br><li>")

    # Ensure the entire string is wrapped in a paragraph if it is not a list.
    if not review_text.startswith("<ul>"):
        review_text = f"<p>{review_text}</p>"

    return f"<h1>{title}</h1>{review_text}"

def generate_review(title, abstract, keywords, domain):
    """
    Uses AI to generate a constructive review for the professor's research using Google's Gemini API.
    """
    if not API_KEY:
        return "Error: API key not found in environment variables."

    prompt = f"""
    Title: {title}
    Abstract: {abstract}
    Keywords: {keywords}
    Domain: {domain}

    Provide a professional research review highlighting strengths, areas for improvement, and potential future directions.
    """

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(f"{API_URL}?key={API_KEY}", json=data, headers=headers)
        response.raise_for_status()
        response_json = response.json()

        candidates = response_json.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                review_text = parts[0].get("text", "No response")
                print(review_text)
                return format_review_as_html(review_text,title)  # Convert to HTML format
            else:
                return "Error: No parts in content."
        else:
            return "Error: No candidates in response."

    except requests.exceptions.RequestException as e:
        return f"Error: Request failed - {e}"
    except ValueError:
        return f"Error: Invalid JSON response - {response.text}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {e}"

# Example Usage:
# print(generate_review("AI in Medicine", "Research on AI's impact in healthcare.", "AI, Medicine, Deep Learning", "Healthcare"))



@app.route("/review", methods=["GET", "POST"])
def review():
    if request.method == "POST":
        title = request.form["title"]
        abstract = request.form["abstract"]
        keywords = request.form["keywords"]
        domain = request.form["domain"]

        if not title or not abstract:
            flash("Title and Abstract are required!", "error")
            return redirect(url_for("review"))

        review_feedback = generate_review(title, abstract, keywords, domain)

        return render_template("output.html", review_feedback=review_feedback)

    return render_template("review.html")

if __name__ == '__main__':
    app.run(debug=True)

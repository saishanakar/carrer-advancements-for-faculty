from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = 'your_secure_random_secret_key'

# MongoDB Setup
MONGO_URI = "mongodb+srv://asaninnovatorsprojectguide:bXsxafE4YWAn0bRb@cluster0.ikhda.mongodb.net/faculty_portal?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["faculty_portal"]
teachers_collection = db["teachers"]

# Load dataset & train model on startup
file_path = "data/preprocessed_data.csv"  # Ensure this file exists
df = pd.read_csv(file_path)

# Define Target Column
target_column = "Future Designation"  # Change this if needed
X = df.drop(columns=["New Designation", "Future Designation"])  # Drop both target columns
y = df[target_column]

# Encode categorical columns
label_encoders = {}
for col in X.select_dtypes(include=["object"]).columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])
    label_encoders[col] = le  # Store encoders for use during prediction

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class FacultyForm(FlaskForm):
    years_of_service = IntegerField("Years of Service", validators=[DataRequired()])
    academic_qual = SelectField("Academic Qualification", choices=["PhD", "MSc", "MBA", "BTech"], validators=[DataRequired()])
    publication_count = IntegerField("Publication Count (Journals)", validators=[DataRequired()])
    citation_metrics = FloatField("Citation Metrics", validators=[DataRequired()])
    communication_clarity = IntegerField("Communication Clarity (1-10)", validators=[DataRequired()])
    core_courses_count = IntegerField("Core Courses Count (CS)", validators=[DataRequired()])
    course_completion_effectiveness = IntegerField("Course Completion Effectiveness (1-10)", validators=[DataRequired()])
    current_designation = SelectField("Current Designation", choices=["Assistant Professor", "Associate Professor", "Professor"], validators=[DataRequired()])
    student_engagement = IntegerField("Student Engagement (1-10)", validators=[DataRequired()])
    research_projects = IntegerField("Research Project Involvement", validators=[DataRequired()])
    teaching_innovation = IntegerField("Teaching Innovation Metrics (1-10)", validators=[DataRequired()])
    patent_count = IntegerField("Patent Count", validators=[DataRequired()])
    submit = SubmitField("Predict Designation")

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.password.data)

        if teachers_collection.find_one({"username": username}):
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        teachers_collection.insert_one({"username": username, "password": password})
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = teachers_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('teacher_dashboard'))
        else:
            flash("Invalid username or password!", "danger")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/teacher', methods=['GET', 'POST'])
def teacher_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    form = FacultyForm()
    prediction = None

    # Define a mapping for designations to integers
    designation_mapping = {
        "Assistant Professor": 0,
        "Associate Professor": 1,
        "Professor": 2
    }

    if form.validate_on_submit():
        user_data = {
            "Years of Service": form.years_of_service.data,
            "Academic Qualifications": form.academic_qual.data,
            "Publication Records (Journals)": form.publication_count.data,
            "Citation Metrics": form.citation_metrics.data,
            "Communication Clarity (1-10)": form.communication_clarity.data,
            "Core Courses Count (CS)": form.core_courses_count.data,
            "Course Completion Effectiveness (1-10)": form.course_completion_effectiveness.data,
            "Current Designation": designation_mapping.get(form.current_designation.data, -1),  # Convert to integer
            "Student Engagement (1-10)": form.student_engagement.data,
            "Research Project Involvement": form.research_projects.data,
            "Teaching Innovation Metrics (1-10)": form.teaching_innovation.data,
            "Patent Count": form.patent_count.data,
        }

        # Convert user input into DataFrame
        input_df = pd.DataFrame([user_data])

        # Apply label encoding for categorical columns
        for col in input_df.columns:
            if col in label_encoders:
                input_df[col] = label_encoders[col].transform(input_df[col].astype(str))

        # Ensure input matches model's training features
        input_df = input_df.reindex(columns=X.columns, fill_value=0)

        # Debugging: Print the input DataFrame before prediction
        print("Processed Input DataFrame before prediction:\n", input_df)

        # Make Prediction
        prediction = model.predict(input_df)[0]

    return render_template('teacher_dashboard.html', form=form, prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

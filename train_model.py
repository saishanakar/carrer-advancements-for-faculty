## train_model.py

import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load dataset
df = pd.read_csv("data\preprocessed_data.csv") # Update with actual dataset path

# Define features and target
FEATURES = ["Years of Service", "Patent Count", "Publication Records (Journals)",
            "Publication Records (Conferences)", "Student Engagement (1-10)",
            "Doubt Resolution (1-10)", "Teaching Innovation Metrics (1-10)",
            "Student Success Rates (1-10)"]
TARGET = "Future Designation"

# Ensure the target variable is properly encoded
# Convert target variable to numeric values
designation_mapping = {
    0: "Assistant Professor",
    1: "Associate Professor",
    2: "Professor",
    3: "HOD",
    4: "Senior Lecturer",
    5: "Lecturer",
    6: "Junior Lecturer"
}



X = df[FEATURES]
y = df[TARGET]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save the trained model
with open("faculty_prediction_model.pkl", "wb") as file:
    pickle.dump(model, file)

print("✅ Model saved as faculty_prediction_model.pkl")

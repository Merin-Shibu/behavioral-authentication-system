from flask import Flask, render_template, request, jsonify
import json
import os
from sklearn.svm import OneClassSVM

app = Flask(__name__)

DATA_FILE = "users.json"

# -----------------------------
# Load users
# -----------------------------
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# -----------------------------
# Save users
# -----------------------------
def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# -----------------------------
# Home
# -----------------------------
@app.route('/')
def home():
    return render_template("index.html")

# -----------------------------
# Register
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data['username']
    password = data['password']
    keystrokes = data['keystrokes']

    users = load_users()

    if username not in users:
        users[username] = {
            "password": password,
            "patterns": []
        }

    users[username]["patterns"].append(keystrokes)

    save_users(users)

    return jsonify({"message": "Sample saved ✅ (Register 5-7 times)"})

# -----------------------------
# Login (HYBRID SYSTEM)
# -----------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data['username']
    password = data['password']
    keystrokes = data['keystrokes']

    users = load_users()

    if username not in users:
        return jsonify({"message": "User not found!"})

    stored = users[username]

    if password != stored["password"]:
        return jsonify({"message": "Wrong password!"})

    patterns = stored["patterns"]

    # -------------------------
    # RULE-BASED SCORING
    # -------------------------
    scores = []

    for pattern in patterns:
        min_len = min(len(pattern), len(keystrokes))

        diff = sum(abs(pattern[i] - keystrokes[i]) for i in range(min_len))
        diff = diff / min_len if min_len > 0 else 9999

        scores.append(diff)

    valid_scores = [s for s in scores if s < 1000]

    if not valid_scores:
        return jsonify({"message": "Insufficient data ❌"})

    best_score = min(valid_scores)
    avg_score = sum(valid_scores) / len(valid_scores)

    # Adjust these if needed
    rule_pass = (best_score < 180 and avg_score < 400)

    # -------------------------
    # AI MODEL (SVM)
    # -------------------------
    clean_patterns = [p for p in patterns if len(p) > 0]

    prediction = -1

    if len(clean_patterns) >= 3:
        min_len = min(len(p) for p in clean_patterns)

        trimmed = [p[:min_len] for p in clean_patterns]

        model = OneClassSVM(gamma='auto', nu=0.5)
        model.fit(trimmed)

        if len(keystrokes) >= min_len:
            test_sample = [keystrokes[:min_len]]
            prediction = model.predict(test_sample)[0]

    ai_pass = (prediction == 1)

    # -------------------------
    # FINAL DECISION
    # -------------------------
    print("----- FINAL ANALYSIS -----")
    print("Best score:", best_score)
    print("Avg score:", avg_score)
    print("Rule pass:", rule_pass)
    print("AI prediction:", prediction)

    if rule_pass or ai_pass:
        return jsonify({"message": "Login successful ✅"})
    else:
        return jsonify({"message": "Behavior mismatch ❌"})

# -----------------------------
# Run
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
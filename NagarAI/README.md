# NagarAI — Flask AI Public Infrastructure & Governance Project

NagarAI is a beginner-friendly Flask project demonstrating how AI can help classify citizen complaints and recommend transparent priority levels.

## Features

- Citizen complaint submission
- NLP complaint classification using TF-IDF + Logistic Regression
- Fallback keyword classifier if the trained model is unavailable
- Transparent priority score using severity, public impact, and affected population
- SQLite database
- Dashboard with totals and issue categories
- Complaint filtering
- Status management: Pending / In Progress / Resolved
- Bootstrap responsive interface

## 1. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Train the AI model

```bash
python train_model.py
```

This creates:

`models/complaint_classifier.pkl`

## 4. Run the Flask application

```bash
python app.py
```

Open:

`http://127.0.0.1:5000`

## Deploy to Vercel

This project is configured for Vercel using a serverless Python entry point.

1. Push this repository to GitHub.
2. Import the repo in Vercel.
3. Keep the default Python settings.
4. Add a secret if you want a custom Flask session key:

```bash
SECRET_KEY=your-secret-key
```

The app stores its SQLite database in `/tmp/nagarai.db` on Vercel so it can work in the serverless environment.

## Project structure

```text
NagarAI/
├── app.py
├── ai_model.py
├── train_model.py
├── requirements.txt
├── README.md
├── data/
│   └── complaints.csv
├── models/
│   └── complaint_classifier.pkl   # created after training
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── submit.html
│   ├── submitted.html
│   ├── complaints.html
│   └── about.html
└── static/
```

## Priority logic

The prototype uses:

- Severity: 40%
- Public impact: 35%
- Affected people: 25%

Priority:

- 4.2+ → Critical
- 3.3–4.19 → High
- 2.2–3.29 → Medium
- Below 2.2 → Low

## Notes for a real deployment

This is an educational prototype. A production municipal system should add authentication and authorization, secure secrets, HTTPS, CSRF protection, input validation, rate limiting, audit logs, encrypted sensitive data where appropriate, backups, monitoring, model evaluation, human review, and formal governance/privacy controls.

The sample dataset is intentionally small. For a stronger AI model, collect and label a larger, representative dataset from the target municipality and evaluate it on a held-out test set.

from flask import Flask, render_template, request, jsonify
import pandas as pd
from pathlib import Path
import random

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets"

MONTH_FILES = {
    "August": "august.csv",
    "September": "september.csv",
    "October": "october.csv",
    "November": "november.csv",
}

# In-memory storage for budget limit
user_budget = {"limit": 10000.0}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/monthly-summary")
def monthly_summary():
    results = []
    prev_total = None
    prev_categories = {}

    for month, filename in MONTH_FILES.items():
        file_path = DATASET_DIR / filename

        if not file_path.exists():
            return jsonify({"error": f"Dataset not found: {filename}"}), 404

        df = pd.read_csv(file_path)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        total = float(df["amount"].sum())
        transaction_count = int(len(df))
        category_totals = df.groupby("category")["amount"].sum().to_dict()
        
        transactions = []
        for idx, row in df.iterrows():
            transactions.append({
                "index": int(idx),
                "date": str(row.get("date", "")),
                "category": str(row.get("category", "")),
                "amount": float(row.get("amount", 0))
            })

        pct_change = None
        if prev_total is not None and prev_total > 0:
            pct_change = round(((total - prev_total) / prev_total) * 100, 1)

        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        top_category = sorted_categories[0][0] if sorted_categories else "None"
        top_category_amount = sorted_categories[0][1] if sorted_categories else 0.0

        if top_category_amount > (total * 0.35) and total > 0:
            suggestion = f"You spent heavily on {top_category} this month ({round((top_category_amount/total)*100)}% of total expenses). Try budgeting a 15% reduction here next month."
        else:
            suggestion = "Your spending distribution across categories is well-balanced. Keep up consistent tracking!"

        formatted_categories = {cat: round(float(amt), 2) for cat, amt in category_totals.items()}

        results.append({
            "month": month,
            "total": round(total, 2),
            "budget": user_budget["limit"],
            "transaction_count": transaction_count,
            "comparison_pct": pct_change,
            "top_category": top_category,
            "saving_suggestion": suggestion,
            "categories": formatted_categories,
            "prev_categories": prev_categories,
            "transactions": transactions
        })
        
        prev_total = total
        prev_categories = formatted_categories

    return jsonify(results)

@app.route("/api/update-budget", methods=["POST"])
def update_budget():
    data = request.get_json()
    new_budget = data.get("budget")
    if new_budget is not None:
        user_budget["limit"] = float(new_budget)
        return jsonify({"success": True, "budget": user_budget["limit"]})
    return jsonify({"success": False, "error": "Invalid budget value"}), 400

@app.route("/api/add-expense", methods=["POST"])
def add_expense():
    data = request.get_json()
    month = data.get("month")
    date = data.get("date")
    category = data.get("category")
    amount = data.get("amount")

    if not all([month, date, category, amount]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    filename = MONTH_FILES.get(month)
    if not filename:
        return jsonify({"success": False, "error": "Invalid month"}), 400

    file_path = DATASET_DIR / filename
    
    if file_path.exists():
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=["date", "category", "amount"])

    new_row = pd.DataFrame([{"date": date, "category": category, "amount": float(amount)}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(file_path, index=False)

    return jsonify({"success": True})

@app.route("/api/delete-expense", methods=["POST"])
def delete_expense():
    data = request.get_json()
    month = data.get("month")
    index = data.get("index")

    if month is None or index is None:
        return jsonify({"success": False, "error": "Missing month or index"}), 400

    filename = MONTH_FILES.get(month)
    if not filename:
        return jsonify({"success": False, "error": "Invalid month"}), 400

    file_path = DATASET_DIR / filename
    if file_path.exists():
        df = pd.read_csv(file_path)
        if 0 <= index < len(df):
            df = df.drop(index).reset_index(drop=True)
            df.to_csv(file_path, index=False)
            return jsonify({"success": True})

    return jsonify({"success": False, "error": "Transaction not found"}), 404

@app.route("/api/iot-meter", methods=["GET"])
def get_iot_meter():
    units = random.randint(90, 180)
    tariff_rate = 8.0
    return jsonify({
        "units": units,
        "rate": tariff_rate,
        "estimated_cost": round(units * tariff_rate, 2),
        "status": "connected"
    })

if __name__ == "__main__":
    app.run(debug=True)

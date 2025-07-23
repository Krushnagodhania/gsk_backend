from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import psycopg
from decimal import Decimal

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://avnadmin:AVNS_B3cVlMKO-MgS-6n12xx@pg-2c83c380-gsk2025.c.aivencloud.com:27580/defaultdb?sslmode=require")

def get_db_connection():
    return psycopg.connect(DATABASE_URL)

@app.route("/", methods=["GET"])
def read_root():
    return jsonify({"message": "Flask is running!"})


@app.route("/addresses", methods=["GET"])
def get_addresses():
    street = request.args.get("street")
    if not street:
        return jsonify({"error": "Street parameter is required"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT * FROM GSK_TABLE
                    WHERE address ILIKE %s
                """
                cur.execute(query, (f"%{street}%",))
                rows = cur.fetchall()

                colnames = [desc[0] for desc in cur.description]
                results = [dict(zip(colnames, row)) for row in rows]

                return jsonify({"matches": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/submit", methods=["POST"])
def submit_form():
    try:
        data = request.get_json()

        address = data.get("address")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone = data.get("phone")
        email = data.get("email")
        eligibility_type = data.get("eligibility_type")
        income_details = json.dumps(data.get("income_details", []))
        total_income = data.get("total_income")
        benefit_description = data.get("benefit_description")
        benefit_images = data.get("benefit_images")
        qualifications = json.dumps(data.get("qualifications", []))
        accepted = True

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE GSK_TABLE SET
                        first_name = %s,
                        last_name = %s,
                        phone = %s,
                        email = %s,
                        eligibility_type = %s,
                        income_details = %s,
                        total_income = %s,
                        benefit_description = %s,
                        benefit_images = %s,
                        what_we_can_do = %s,
                        accepted = %s
                    WHERE address = %s
                """, (
                    first_name,
                    last_name,
                    phone,
                    email,
                    eligibility_type,
                    income_details,
                    total_income,
                    benefit_description,
                    benefit_images,
                    qualifications,
                    accepted,
                    address
                ))

        return jsonify({"message": "Row updated successfully"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/get-by-address", methods=["GET"])
def get_by_address():
    address = request.args.get("address")
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT address, first_name, last_name, phone, email,
                           eligibility_type, income_details, total_income,
                           benefit_description, benefit_images, what_we_can_do
                    FROM GSK_TABLE
                    WHERE address = %s
                """, (address,))
                
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Address not found"}), 404

                colnames = [desc[0] for desc in cur.description]
                result = dict(zip(colnames, row))

                if result.get("income_details"):
                    try:
                        result["income_details"] = json.loads(result["income_details"])
                    except:
                        pass

                return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/qualified-entries", methods=["GET"])
def qualified_entries():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM GSK_TABLE WHERE accepted = true AND completed = false
                """)
                
                rows = cur.fetchall()
                if not rows:
                    return jsonify({"error": "No qualified entries found"}), 404

                colnames = [desc[0] for desc in cur.description]
                results = []
                for row in rows:
                    result = dict(zip(colnames, row))

                    if result.get("income_details"):
                        try:
                            result["income_details"] = json.loads(result["income_details"])
                        except:
                            pass
                    
                    if result.get("what_we_can_do"):
                        try:
                            result["what_we_can_do"] = json.loads(result["what_we_can_do"])
                        except:
                            pass

                    if isinstance(result.get("total_income"), Decimal):
                        result["total_income"] = float(result["total_income"])

                    results.append(result)

                return jsonify({"qualified_entries": results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

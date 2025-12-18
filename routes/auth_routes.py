from flask import Blueprint, request, session, jsonify, render_template
from services.db_service import get_db_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    supplier_code = data.get("supplier_code")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CUSTID, NAME
        FROM party
        WHERE UNDERPRIMENO = 27
        AND CUSTID = ?
    """, supplier_code)

    row = cursor.fetchone()
    conn.close()

    if row:
        session["supplier_code"] = row.CUSTID
        session["supplier_name"] = row.NAME
        return jsonify({"success": True})

    return jsonify({"success": False})

from flask import Blueprint, session, jsonify, render_template, redirect, request
from services.db_service import get_db_connection
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

# =========================================================
# DASHBOARD PAGE
# =========================================================
@dashboard_bp.route("/dashboard")
def dashboard():
    if "supplier_code" not in session:
        return redirect("/")
    return render_template(
        "dashboard.html",
        supplier_name=session.get("supplier_name")
    )

# =========================================================
# MAIN SALES (ORDERED / SUPPLIED / REMAINING)
# =========================================================
@dashboard_bp.route("/api/sales")
def sales_data():
    if "supplier_code" not in session:
        return jsonify([])

    from_daten = int(request.args["from"].replace("-", ""))
    to_daten   = int(request.args["to"].replace("-", ""))
    supplier_code = session["supplier_code"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            g.code,
            g.code2,
            SUM(s.qty) AS ordered_qty,

            ISNULL((
                SELECT SUM(st.qty)
                FROM stock st
                WHERE st.boxcd = g.code
                  AND st.trnflag = 'P'
                  AND st.daten BETWEEN ? AND ?
            ),0) AS supplied_qty

        FROM group3 g
        JOIN stocktrn s ON g.code = s.group2
        WHERE s.charity BETWEEN ? AND ?
          AND s.qty <> 0
          AND s.mrp = 0
          AND s.mrp1 = 1
          AND g.custid = ?
        GROUP BY g.code, g.code2
        ORDER BY g.code
    """, (from_daten, to_daten, from_daten, to_daten, supplier_code))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "boxId": r[0],
            "boxName": r[1],
            "ordered": int(r[2]),
            "supplied": int(r[3]),
            "remaining": max(int(r[2]) - int(r[3]), 0)
        }
        for r in rows
    ])

# =========================================================
# COMPANY-WISE REMAINING QTY (NO BRANCH)
# =========================================================
@dashboard_bp.route("/api/branch-breakup")
def branch_breakup():
    if "supplier_code" not in session:
        return jsonify([])

    box_id = int(request.args["boxId"])
    from_daten = int(request.args["from"].replace("-", ""))
    to_daten   = int(request.args["to"].replace("-", ""))
    supplier_code = session["supplier_code"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM (
            SELECT
                s.company,
                SUM(s.qty)
                -
                ISNULL((
                    SELECT SUM(st.qty)
                    FROM stock st
                    WHERE st.boxcd = s.group2
                      AND st.company = s.company
                      AND st.trnflag = 'P'
                      AND st.daten BETWEEN ? AND ?
                ),0) AS remaining_qty

            FROM stocktrn s
            JOIN group3 g ON g.code = s.group2
            WHERE s.group2 = ?
              AND s.charity BETWEEN ? AND ?
              AND s.qty <> 0
              AND s.mrp = 0
              AND s.mrp1 = 1
              AND g.custid = ?
            GROUP BY s.company, s.group2
        ) x
        WHERE x.remaining_qty > 0
        ORDER BY x.company
    """, (
        from_daten, to_daten,
        box_id, from_daten, to_daten, supplier_code
    ))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "company": r[0],
            "qty": int(r[1])
        }
        for r in rows
    ])

# =========================================================
# SAVE SUPPLY (STOCK INSERT)
# =========================================================
@dashboard_bp.route("/api/save-supply", methods=["POST"])
def save_supply():
    if "supplier_code" not in session:
        return jsonify({"success": False})

    data = request.json

    boxcd = int(data["boxId"])
    itemname = data["boxName"]
    qty = int(data["qty"])
    company = data["company"]

    supply_date = data["supplyDate"]
    daten = int(supply_date.replace("-", ""))
    date_ = datetime.strptime(
        supply_date, "%Y-%m-%d"
    ).strftime("%d/%m/%Y")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ISNULL(MAX(srno),0)+1 FROM stock")
    srno = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO stock
        (boxcd, ITEMNAME, qty, date_, daten,
         stock_in, company, srno, trnflag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'P')
    """, (
        boxcd, itemname, qty, date_, daten,
        qty, company, srno
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

from flask import Blueprint, request, jsonify, session, render_template
from services.db_service import get_db_connection
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    if "supplier_code" not in session:
        return render_template("login.html")

    return render_template(
        "dashboard.html",
        supplier_name=session.get("supplier_name")
    )


# =========================================================
# MAIN SALES (ORDERED / SUPPLIED / REMAINING)
# =========================================================
@dashboard_bp.route("/api/sales")
def sales():
    if "supplier_code" not in session:
        return jsonify([])

    from_daten = int(request.args["from"].replace("-", ""))
    to_daten   = int(request.args["to"].replace("-", ""))
    supplier_code = session["supplier_code"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            g.code2 AS box_id,
            g.type  AS box_name,
            SUM(st.qty) AS ordered_qty,
            ISNULL((
                SELECT SUM(s.qty)
                FROM stock s
                WHERE s.boxcd = g.code
                  AND s.trnflag = 'P'
                  AND s.daten BETWEEN ? AND ?
            ), 0) AS supplied_qty
        FROM group3 g
        JOIN stocktrn st ON st.group2 = g.code
        WHERE st.charity BETWEEN ? AND ?
          AND st.qty <> 0
          AND st.mrp = 0
          AND st.mrp1 = 1
          AND g.custid = ?
        GROUP BY g.code, g.code2, g.type
        ORDER BY g.code2
    """, (from_daten, to_daten, from_daten, to_daten, supplier_code))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        ordered = int(r.ordered_qty)
        supplied = int(r.supplied_qty)
        result.append({
            "boxId": r.box_id,
            "boxName": r.box_name,
            "ordered": ordered,
            "supplied": supplied,
            "remaining": max(ordered - supplied, 0)
        })

    return jsonify(result)


# =========================================================
# BRANCH BREAKUP (REMAINING QTY)
# =========================================================
@dashboard_bp.route("/api/branch-breakup")
def branch_breakup():
    if "supplier_code" not in session:
        return jsonify([])

    box_id = request.args["boxId"]
    from_daten = int(request.args["from"].replace("-", ""))
    to_daten   = int(request.args["to"].replace("-", ""))
    supplier_code = session["supplier_code"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.company,
            SUM(s.qty) -
            ISNULL((
                SELECT SUM(st.qty)
                FROM stock st
                WHERE st.boxcd = s.group2
                  AND st.company = s.company
                  AND st.trnflag = 'P'
                  AND st.daten BETWEEN ? AND ?
            ), 0) AS remaining_qty
        FROM stocktrn s
        JOIN group3 g ON g.code = s.group2
        WHERE g.code2 = ?
          AND s.charity BETWEEN ? AND ?
          AND s.qty <> 0
          AND s.mrp = 0
          AND s.mrp1 = 1
          AND g.custid = ?
        GROUP BY s.company, s.group2
        HAVING SUM(s.qty) -
               ISNULL((
                    SELECT SUM(st.qty)
                    FROM stock st
                    WHERE st.boxcd = s.group2
                      AND st.company = s.company
                      AND st.trnflag = 'P'
                      AND st.daten BETWEEN ? AND ?
               ), 0) > 0
        ORDER BY s.company
    """, (
        from_daten, to_daten,
        box_id, from_daten, to_daten, supplier_code,
        from_daten, to_daten
    ))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {"company": r.company, "qty": int(r.remaining_qty)}
        for r in rows
    ])


# =========================================================
# GODOWNS
# =========================================================
@dashboard_bp.route("/api/godowns")
def godowns():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT bname
        FROM branch
        WHERE bname IS NOT NULL
        ORDER BY bname
    """)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([r.bname for r in rows])


# =========================================================
# SAVE SUPPLY
# =========================================================
@dashboard_bp.route("/api/save-supply", methods=["POST"])
def save_supply():
    if "supplier_code" not in session:
        return jsonify({"success": False})

    data = request.json

    box_id = data["boxId"]
    box_name = data["boxName"]
    qty = int(data["qty"])
    company = data["company"]
    godown = data["godown"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT code FROM group3 WHERE code2 = ?", box_id)
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False})

    boxcd = row.code

    today = datetime.strptime("2015-12-18", "%Y-%m-%d")
    date_ = today.strftime("%d/%m/%Y")
    daten = int(today.strftime("%Y%m%d"))

    cursor.execute("SELECT ISNULL(MAX(srno),0)+1 FROM stock")
    srno = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO stock (
            boxcd, ITEMNAME, qty,
            date_, daten, stock_in,
            company, srno, trnflag, godown
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'P', ?)
    """, (
        boxcd, box_name, qty,
        date_, daten, qty,
        company, srno, godown
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

from flask import Blueprint, session, jsonify, render_template, redirect, request
from services.db_service import get_db_connection
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

# =========================================================
# 1️⃣ DASHBOARD PAGE
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
# 2️⃣ MAIN SALES API (REMAINING QTY)
# =========================================================
@dashboard_bp.route("/api/sales")
def sales_data():
    if "supplier_code" not in session:
        return jsonify([])

    from_date = request.args.get("from")
    to_date = request.args.get("to")

    if not from_date or not to_date:
        return jsonify([])

    from_date = from_date.replace("-", "")
    to_date = to_date.replace("-", "")

    supplier_code = session["supplier_code"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            g.code AS box_id,
            g.code2 AS box_name,

            SUM(s.qty) AS ordered_qty,

            ISNULL((
                SELECT SUM(st.qty)
                FROM stock st
                WHERE 
                    st.boxcd = g.code
                    AND st.daten BETWEEN ? AND ?
                    AND st.trnflag = 'P'
            ), 0) AS supplied_qty

        FROM group3 g
        JOIN stocktrn s ON g.code = s.group2
        WHERE 
            s.charity BETWEEN ? AND ?
            AND s.qty <> 0
            AND s.mrp = 0
            AND s.mrp1 = 1
            AND g.custid = ?
        GROUP BY g.code, g.code2
        ORDER BY g.code
    """, (from_date, to_date, from_date, to_date, supplier_code))

    rows = cursor.fetchall()
    conn.close()

    result = []

    for r in rows:
        ordered = r[2]
        supplied = r[3]
        remaining = max(ordered - supplied, 0)

        result.append({
            "boxId": r[0],
            "boxName": r[1],
            "ordered": ordered,
            "supplied": supplied,
            "remaining": remaining
        })

    return jsonify(result)

# =========================================================
# 3️⃣ BRANCH-WISE BREAKUP (ORDERED QTY)
# =========================================================
@dashboard_bp.route("/api/branch-breakup")
def branch_breakup():
    if "supplier_code" not in session:
        return jsonify([])

    box_id = request.args.get("boxId")
    from_date = request.args.get("from")
    to_date = request.args.get("to")

    if not box_id or not from_date or not to_date:
        return jsonify([])

    from_date = from_date.replace("-", "")
    to_date = to_date.replace("-", "")

    supplier_code = session["supplier_code"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            s.company,
            s.branchcode,
            SUM(s.qty) AS qty
        FROM stocktrn s
        JOIN group3 g ON g.code = s.group2
        WHERE 
            s.group2 = ?
            AND s.charity BETWEEN ? AND ?
            AND s.qty <> 0
            AND s.mrp = 0
            AND s.mrp1 = 1
            AND g.custid = ?
        GROUP BY s.company, s.branchcode
        ORDER BY s.company, s.branchcode
    """, (box_id, from_date, to_date, supplier_code))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "company": r[0],
            "branch": r[1],
            "qty": r[2]
        }
        for r in rows
    ])

# =========================================================
# 4️⃣ SAVE SUPPLIER SUPPLY (WRITE VIEW)
# =========================================================
@dashboard_bp.route("/api/save-supply", methods=["POST"])
def save_supply():
    if "supplier_code" not in session:
        return jsonify({"success": False, "msg": "Unauthorized"})

    data = request.json

    try:
        boxcd = data["boxId"]
        itemname = data["boxName"]
        qty = int(data["qty"])
        branchcode = data["branchcode"]
        company = data["company"]
    except:
        return jsonify({"success": False, "msg": "Invalid data"})

    if qty <= 0:
        return jsonify({"success": False, "msg": "Quantity must be greater than zero"})

    today = datetime.now()
    date_ = today.strftime("%d/%m/%Y")
    daten = int(today.strftime("%Y%m%d"))
    trnflag = "P"

    # Stock_in logic (safe default)
    stock_in = qty

    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate SRNO safely
    cursor.execute("SELECT ISNULL(MAX(srno), 0) + 1 FROM stock")
    srno = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO stock
        (
            boxcd,
            itemname,
            qty,
            date_,
            daten,
            stock_in,
            branchcode,
            company,
            srno,
            trnflag
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        boxcd,
        itemname,
        qty,
        date_,
        daten,
        stock_in,
        branchcode,
        company,
        srno,
        trnflag
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

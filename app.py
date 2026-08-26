
from flask import Flask, jsonify, request, render_template
import sqlite3, os, csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dhaniti.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__)

STATUS_ORDER = ["Submitted", "Under Review", "Approved", "Rejected"]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS institutions(
      institution_id TEXT PRIMARY KEY, institution_name TEXT NOT NULL,
      city TEXT, state TEXT, institution_type TEXT
    );
    CREATE TABLE IF NOT EXISTS courses(
      course_id TEXT PRIMARY KEY, course_name TEXT NOT NULL, domain TEXT,
      typical_fee_inr REAL, duration_months INTEGER
    );
    CREATE TABLE IF NOT EXISTS applications(
      application_id TEXT PRIMARY KEY, student_name TEXT NOT NULL, age INTEGER,
      student_state TEXT, institution_id TEXT, institution_name TEXT,
      course_id TEXT, course_name TEXT, course_domain TEXT, course_fee_inr REAL,
      loan_amount_requested_inr REAL, parent_monthly_income_inr REAL,
      existing_monthly_obligations_inr REAL, credit_score REAL,
      employment_type TEXT, application_date TEXT, application_status TEXT,
      application_channel TEXT,
      FOREIGN KEY(institution_id) REFERENCES institutions(institution_id),
      FOREIGN KEY(course_id) REFERENCES courses(course_id)
    );
    """)
    if cur.execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 0:
        load_seed(cur)
    conn.commit(); conn.close()

def clean_text(v):
    return v.strip() if isinstance(v, str) else v

def load_seed(cur):
    # Load master data first; IDs are the source of truth for names.
    with open(os.path.join(DATA_DIR,"institutions.csv"), newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            cur.execute("INSERT INTO institutions VALUES (?,?,?,?,?)",
                        (r["institution_id"].strip(), clean_text(r["institution_name"]),
                         clean_text(r["city"]), clean_text(r["state"]), clean_text(r["institution_type"])))
    with open(os.path.join(DATA_DIR,"courses.csv"), newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            cur.execute("INSERT INTO courses VALUES (?,?,?,?,?)",
                        (r["course_id"].strip(), clean_text(r["course_name"]), clean_text(r["domain"]),
                         float(r["typical_fee_inr"]), int(r["duration_months"])))
    inst = {r["institution_id"]: r["institution_name"] for r in cur.execute("SELECT institution_id,institution_name FROM institutions")}
    courses = {r["course_id"]: r["course_name"] for r in cur.execute("SELECT course_id,course_name FROM courses")}
    with open(os.path.join(DATA_DIR,"applications.csv"), newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            iid, cid = r["institution_id"].strip(), r["course_id"].strip()
            # Data-quality handling: trim strings, use master names by ID, retain missing credit score as NULL.
            vals = (
                r["application_id"].strip(), clean_text(r["student_name"]), int(r["age"]),
                clean_text(r["student_state"]), iid, inst.get(iid, clean_text(r["institution_name"])),
                cid, courses.get(cid, clean_text(r["course_name"])), clean_text(r["course_domain"]),
                float(r["course_fee_inr"]), float(r["loan_amount_requested_inr"]),
                float(r["parent_monthly_income_inr"]), float(r["existing_monthly_obligations_inr"]),
                float(r["credit_score"]) if r["credit_score"] not in ("", None) else None,
                clean_text(r["employment_type"]), r["application_date"],
                clean_text(r["application_status"]), clean_text(r["application_channel"])
            )
            cur.execute("INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)

# Initialize the database when the module is imported by Gunicorn/Render.
# Gunicorn does not execute the __main__ block.
init_db()

def rows(sql, params=()):
    conn=db()
    data=[dict(r) for r in conn.execute(sql,params).fetchall()]
    conn.close(); return data

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/dashboard")
def dashboard():
    conn=db()
    total=conn.execute("SELECT COUNT(*) n FROM applications").fetchone()["n"]
    loan=conn.execute("SELECT COALESCE(SUM(loan_amount_requested_inr),0) n FROM applications").fetchone()["n"]
    status=[dict(r) for r in conn.execute(
        "SELECT application_status status, COUNT(*) count, COALESCE(SUM(loan_amount_requested_inr),0) loan FROM applications GROUP BY application_status"
    )]
    course=[dict(r) for r in conn.execute(
        "SELECT course_name name, COUNT(*) count FROM applications GROUP BY course_name ORDER BY count DESC"
    )]
    institution=[dict(r) for r in conn.execute(
        "SELECT institution_name name, COUNT(*) count FROM applications GROUP BY institution_name ORDER BY count DESC"
    )]
    monthly=[dict(r) for r in conn.execute(
        "SELECT substr(application_date,1,7) month, COUNT(*) count FROM applications GROUP BY month ORDER BY month"
    )]
    credit=[dict(r) for r in conn.execute("""
      SELECT CASE
       WHEN credit_score < 600 THEN '<600'
       WHEN credit_score < 650 THEN '600-649'
       WHEN credit_score < 700 THEN '650-699'
       WHEN credit_score < 750 THEN '700-749'
       ELSE '750+'
      END bucket, COUNT(*) count
      FROM applications WHERE credit_score IS NOT NULL GROUP BY bucket
      ORDER BY CASE bucket WHEN '<600' THEN 1 WHEN '600-649' THEN 2 WHEN '650-699' THEN 3 WHEN '700-749' THEN 4 ELSE 5 END
    """)]
    conn.close()
    status_map={x["status"]:x["count"] for x in status}
    return jsonify({"total":total,"loan_total":loan,
                    "approved":status_map.get("Approved",0),
                    "under_review":status_map.get("Under Review",0),
                    "rejected":status_map.get("Rejected",0),
                    "status":status,"course":course,"institution":institution,
                    "monthly":monthly,"credit":credit})

@app.route("/api/applications")
def applications():
    q=request.args.get("q","").strip()
    status=request.args.get("status","").strip()
    course=request.args.get("course","").strip()
    institution=request.args.get("institution","").strip()
    sort=request.args.get("sort","application_date")
    direction=request.args.get("direction","desc").lower()
    allowed={"loan_amount_requested_inr","credit_score","application_date","student_name","application_id"}
    if sort not in allowed: sort="application_date"
    direction="ASC" if direction=="asc" else "DESC"
    sql="SELECT * FROM applications WHERE 1=1"
    params=[]
    if q:
        sql+=" AND (LOWER(application_id) LIKE LOWER(?) OR LOWER(student_name) LIKE LOWER(?))"
        params += [f"%{q}%",f"%{q}%"]
    if status: sql+=" AND application_status=?"; params.append(status)
    if course: sql+=" AND course_name=?"; params.append(course)
    if institution: sql+=" AND institution_name=?"; params.append(institution)
    sql += f" ORDER BY {sort} {direction}, application_id ASC"
    return jsonify(rows(sql,params))

@app.route("/api/applications/<application_id>")
def get_application(application_id):
    data=rows("SELECT * FROM applications WHERE application_id=?",(application_id,))
    if not data: return jsonify({"error":"Application not found"}),404
    return jsonify(data[0])

@app.route("/api/applications", methods=["POST"])
def create_application():
    d=request.get_json(force=True)
    required=["application_id","student_name","age","student_state","institution_id","course_id",
              "course_fee_inr","loan_amount_requested_inr","parent_monthly_income_inr",
              "existing_monthly_obligations_inr","employment_type","application_date",
              "application_channel"]
    missing=[x for x in required if d.get(x) in (None,"")]
    if missing: return jsonify({"error":"Missing fields","fields":missing}),400
    conn=db()
    try:
        inst=conn.execute("SELECT institution_name FROM institutions WHERE institution_id=?",(d["institution_id"],)).fetchone()
        crs=conn.execute("SELECT course_name,domain FROM courses WHERE course_id=?",(d["course_id"],)).fetchone()
        if not inst or not crs: return jsonify({"error":"Invalid institution_id or course_id"}),400
        conn.execute("""INSERT INTO applications
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d["application_id"].strip(),d["student_name"].strip(),int(d["age"]),d["student_state"].strip(),
         d["institution_id"],inst["institution_name"],d["course_id"],crs["course_name"],crs["domain"],
         float(d["course_fee_inr"]),float(d["loan_amount_requested_inr"]),float(d["parent_monthly_income_inr"]),
         float(d["existing_monthly_obligations_inr"]),float(d["credit_score"]) if d.get("credit_score") not in (None,"") else None,
         d["employment_type"].strip(),d["application_date"],d.get("application_status","Submitted").strip(),
         d["application_channel"].strip()))
        conn.commit()
    except sqlite3.IntegrityError as e:
        return jsonify({"error":"Application ID already exists"}),409
    finally: conn.close()
    return jsonify({"message":"Application created"}),201

@app.route("/api/applications/<application_id>/status", methods=["PATCH"])
def update_status(application_id):
    d=request.get_json(force=True); status=d.get("status","").strip()
    if status not in STATUS_ORDER: return jsonify({"error":"Invalid status"}),400
    conn=db(); cur=conn.execute("UPDATE applications SET application_status=? WHERE application_id=?",(status,application_id))
    conn.commit(); conn.close()
    if cur.rowcount==0: return jsonify({"error":"Application not found"}),404
    return jsonify({"message":"Status updated","status":status})

@app.route("/api/masters")
def masters():
    return jsonify({
      "institutions": rows("SELECT institution_id,institution_name FROM institutions ORDER BY institution_name"),
      "courses": rows("SELECT course_id,course_name FROM courses ORDER BY course_name"),
      "statuses": STATUS_ORDER
    })

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)

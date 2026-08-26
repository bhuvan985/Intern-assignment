# Dhaniti Education Lending Application Intelligence Dashboard

## Problem understanding
Dhaniti needs a lightweight internal tool to view, search, filter, analyze and manage a synthetic education-loan application pipeline. The assignment prioritizes a working prototype, data quality, useful insights and explainability within one working day.

## Solution overview
This prototype provides:
- KPI dashboard: total applications, approved, under review, rejected, total loan amount requested.
- Five charts: status mix, course mix, institution mix, monthly pipeline, credit-score distribution.
- Search by application ID/student name.
- Filters by status, course and institution.
- Sorting by loan amount, credit score, student or date.
- Application detail view.
- Create application workflow.
- Update application status workflow.
- SQLite persistence.
- Master-data normalization and missing-value handling.
- Business insights and data-quality notes in the dashboard.

## Technology stack
- Python 3
- Flask REST API
- SQLite
- HTML/CSS/JavaScript
- Chart.js (CDN)
- CSV source data exported from the supplied Excel workbook

## How to run
1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
3. Install:
   `pip install -r requirements.txt`
4. Run:
   `python app.py`
5. Open `http://127.0.0.1:5000`
6. The SQLite database is created automatically on first run and seeded from `data/`.

## Alternative Way to Open:
click the link : https://dhaniti-education-leading-dashboard.onrender.com/

## Database/data model
- `institutions`: institution master keyed by `institution_id`
- `courses`: course master keyed by `course_id`
- `applications`: application fact table referencing institution/course IDs
- Application status is stored on the application record.

The application table intentionally keeps the source fields needed for the assignment while using master IDs as the source of truth for institution/course names.

## Data-quality handling
1. **Missing credit score:** EDU1092 has a missing credit score. It is stored as NULL; the application is not assigned a fabricated score. The dashboard excludes NULL from the credit distribution.
2. **Institution name inconsistency:** CRS/INS master naming includes `Central Inst. of Data Science` versus `Central Institute of Data Science` for INS012. The loader resolves institution name from `institution_id`.
3. **Course name inconsistency:** CRS005 appears as `MBA ` in one application while the course master says `BBA`. The loader resolves the displayed course name from `course_id`, preventing an inconsistent label from splitting the course analysis.
4. **Whitespace variant in channel:** the source contains both `Website` and a whitespace-variant `Website `. Text fields are trimmed during loading.

These rules are normalization for this prototype, not lending-policy decisions.

## Business insights
1. 63/150 applications are Approved = 42.0%.
2. Total requested amount is ₹74,935,752 (about ₹7.49 crore), with an average request of about ₹4.996 lakh.
3. Institution Referral has 34 applications and 18 approvals (52.9%), making it the largest acquisition channel by approval count.
4. MBA is the largest course segment with 26 applications, followed by B.Tech with 23.
5. The dataset contains small quality issues that can distort grouping unless master IDs and whitespace normalization are applied.

## Key assumptions
- All data is synthetic as stated by the assignment.
- Institution and course IDs are authoritative for master-name normalization.
- Missing credit scores remain missing.
- No underwriting or lending-policy decision is inferred from the data.
- Status transitions are editable because the assignment requires status update functionality.

## Known limitations
- Authentication/authorization is not implemented.
- SQLite is suitable for a prototype, not a high-concurrency production deployment.
- No automated tests or CI pipeline are included in this 8-hour prototype.
- Charts are client-side and use Chart.js via CDN.
- No production underwriting or risk score is implemented.

## What I would build next with another 3 days
- Role-based access control and audit history for status changes.
- Pagination and server-side export to CSV.
- Automated data-quality validation and error report.
- Unit/API tests and CI.
- Better accessibility, responsive mobile views and loading/error states.
- Deployment with PostgreSQL and containerization.
- Configurable analytics and saved dashboard views.

## Demo flow
1. Show the KPI dashboard and charts.
2. Search for an application by ID/name.
3. Filter by status/course/institution and sort by loan amount.
4. Open an application and update its status.
5. Create a new application.
6. Explain the missing credit score and master-data normalization.
7. Explain one business insight and one technical decision.

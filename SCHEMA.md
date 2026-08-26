# Database Schema

```text
institutions
-------------
institution_id (PK)
institution_name
city
state
institution_type

courses
-------
course_id (PK)
course_name
domain
typical_fee_inr
duration_months

applications
------------
application_id (PK)
student_name
age
student_state
institution_id (FK -> institutions.institution_id)
institution_name
course_id (FK -> courses.course_id)
course_name
course_domain
course_fee_inr
loan_amount_requested_inr
parent_monthly_income_inr
existing_monthly_obligations_inr
credit_score (nullable)
employment_type
application_date
application_status
application_channel
```

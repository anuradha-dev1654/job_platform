import io

from app import create_app
from app.extensions import db
from app.models import Application, CandidateProfile, Company, Job, SavedJob, User


def login_candidate(client, email="profile@example.com"):
    client.post("/auth/register", data={
        "name": "Profile User",
        "email": email,
        "password": "password123",
        "confirm": "password123",
    })
    response = client.post("/auth/login", data={"email": email, "password": "password123"})
    assert response.status_code in (200, 302)


def test_candidate_profile_save_and_pdf_upload():
    app = create_app("test")
    with app.app_context():
        db.create_all()

        client = app.test_client()
        login_candidate(client)

        response = client.post("/candidate/profile/save", data={
            "section": "basic",
            "name": "Updated User",
            "email": "profile@example.com",
            "headline": "Python developer",
            "location": "Ahmedabad",
            "phone": "9876543210",
            "gender": "Male",
            "birthday": "2000-01-02",
        })
        assert response.status_code == 302

        response = client.post("/candidate/profile/save", data={
            "section": "key_skills",
            "skills": "Python, Flask, SQL",
        })
        assert response.status_code == 302

        pdf = io.BytesIO(b"%PDF-1.4\nsample resume")
        pdf.name = "resume.pdf"
        response = client.post(
            "/candidate/profile/resume",
            data={"resume": (pdf, "resume.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 302

        profile = db.session.scalar(db.select(CandidateProfile))
        assert profile is not None
        assert profile.headline == "Python developer"
        assert profile.sections["key_skills"]["skills"] == ["Python", "Flask", "SQL"]
        assert profile.resume_path.startswith("candidates/")


def test_profile_completion_is_calculated_from_saved_information():
    app = create_app("test")
    with app.app_context():
        db.create_all()
        user = User(name="Dynamic Profile", email="dynamic-profile@example.com", role="candidate")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()
        profile = CandidateProfile(
            user_id=user.id,
            headline="Backend Developer",
            location="Ahmedabad",
            phone="9876543210",
            gender="Male",
            sections={"key_skills": {"skills": ["Python", "Flask"]}},
        )
        db.session.add(profile)
        db.session.commit()

        client = app.test_client()
        login_candidate(client, "dynamic-profile@example.com")
        response = client.get("/candidate/profile")
        assert response.status_code == 200
        assert b"25%" in response.data


def test_arbitrary_location_search_and_suggestions():
    app = create_app("test")
    with app.app_context():
        db.create_all()
        user = User(name="Hiring User", email="hiring-location@example.com",
                    role="company")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()
        company = Company(
            user_id=user.id,
            name="Kutch Technology",
            city="Bhuj",
            is_approved=True,
        )
        db.session.add(company)
        db.session.flush()
        db.session.add(Job(
            company_id=company.id,
            title="Python Developer",
            description="Build Flask APIs",
            location="Gandhidham",
        ))
        db.session.commit()

        client = app.test_client()
        response = client.get("/search?loc=Gandhidham")
        assert response.status_code == 200
        assert b"Python Developer" in response.data

        response = client.get("/api/locations?q=Bh")
        assert response.status_code == 200
        assert "Bhuj" in response.get_json()["locations"]


def test_company_job_detail_apply_and_save():
    app = create_app("test")
    with app.app_context():
        db.create_all()

        hiring_user = User(name="Hiring Manager", email="manager@example.com", role="company")
        hiring_user.set_password("password123")
        db.session.add(hiring_user)
        db.session.flush()
        company = Company(
            user_id=hiring_user.id,
            name="Gujarat Python Labs",
            city="Ahmedabad",
            website="https://example.com",
            is_approved=True,
        )
        db.session.add(company)
        db.session.flush()
        job = Job(
            company_id=company.id,
            title="Python Flask Developer",
            description="Build secure REST APIs with Flask and PostgreSQL.",
            location="Ahmedabad",
        )
        db.session.add(job)
        db.session.commit()

        client = app.test_client()
        login_candidate(client, "apply-profile@example.com")

        response = client.get(f"/company/{company.id}")
        assert response.status_code == 200
        assert b"Gujarat Python Labs" in response.data

        response = client.get(f"/job/{job.id}")
        assert response.status_code == 200
        assert b"Python Flask Developer" in response.data
        assert b"Apply" in response.data

        response = client.post(f"/job/{job.id}/apply", data={
            "phone": "9876543210",
            "experience": "Fresher",
            "cover_letter": "I have experience building Flask applications.",
        })
        assert response.status_code == 302
        application = db.session.scalar(db.select(Application))
        assert application is not None
        assert application.job_id == job.id
        assert application.status == "applied"

        response = client.post(f"/job/{job.id}/save")
        assert response.status_code == 302
        assert db.session.scalar(db.select(SavedJob)) is not None


def test_company_can_save_profile_and_post_detailed_job():
    app = create_app("test")
    with app.app_context():
        db.create_all()
        user = User(name="Company Owner", email="detail-company@example.com", role="company")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()
        company = Company(
            user_id=user.id,
            name="Detail Technology",
            city="Rajkot",
            is_approved=True,
        )
        db.session.add(company)
        db.session.commit()

        client = app.test_client()
        login_response = client.post("/auth/login", data={
            "email": "detail-company@example.com",
            "password": "password123",
        })
        assert login_response.status_code in (200, 302)

        profile_response = client.post("/company/dashboard", data={
            "action": "update_profile",
            "website": "https://detail.example.com",
            "city": "Rajkot",
            "industry": "Information Technology",
            "company_size": "100-200 employees",
            "founded_year": "2020",
            "rating": "4.4",
            "description": "A software company building reliable enterprise products.",
            "address": "Rajkot, Gujarat",
            "benefits": "Health insurance, Remote work",
        })
        assert profile_response.status_code == 302

        job_response = client.post("/company/dashboard", data={
            "title": "Backend Engineer",
            "location": "Rajkot",
            "description": "Build APIs and database-backed backend services.",
            "salary": "₹5 - ₹9 LPA",
            "experience": "1 - 3 years",
            "openings": "3",
            "role": "Backend Development",
            "department": "Engineering",
            "employment_type": "Full Time",
            "role_category": "Software Development",
            "ug_qualification": "B.Tech / B.E. / BCA",
            "pg_qualification": "MCA",
            "key_skills": "Python, Flask, PostgreSQL",
        })
        assert job_response.status_code == 302

        saved_job = db.session.scalar(db.select(Job).where(Job.title == "Backend Engineer"))
        assert saved_job is not None
        assert saved_job.openings == 3
        assert saved_job.key_skills == ["Python", "Flask", "PostgreSQL"]
        assert saved_job.salary == "₹5 - ₹9 LPA"

        detail_response = client.get(f"/job/{saved_job.id}")
        assert detail_response.status_code == 200
        assert b"Backend Engineer" in detail_response.data
        assert b"Backend Development" in detail_response.data


def test_local_company_registration_minimal_data():
    app = create_app("test")
    with app.app_context():
        db.create_all()
        client = app.test_client()

        response = client.post("/auth/register/company", data={
            "rep_name": "Local Admin",
            "rep_email": "local.company@example.com",
            "company_name": "Local Any Company",
            "password": "password123",
            "confirm_password": "password123",
            "confirm_info": "on",
            "agree_terms": "on",
        })

        assert response.status_code in (302, 200)
        company = db.session.scalar(
            db.select(Company).where(Company.name == "Local Any Company")
        )
        assert company is not None
        assert company.is_approved is True
        assert company.corporate_id is None

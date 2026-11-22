import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.models import Company, User


app = create_app("dev")

with app.app_context():
    admin = db.session.scalar(db.select(User).filter_by(email="admin@careerbridge.com"))
    if admin is None:
        admin = db.session.scalar(db.select(User).filter_by(email="admin@careerbridge.local"))
        if admin is not None:
            admin.email = "admin@careerbridge.com"
    if admin is None:
        admin = User(
            name="CareerBridge Admin",
            email="admin@careerbridge.com",
            role="admin",
        )
        admin.set_password("Admin@12345")
        db.session.add(admin)

    company_user = db.session.scalar(
        db.select(User).filter_by(email="company@careerbridge.com")
    )
    if company_user is None:
        company_user = db.session.scalar(
            db.select(User).filter_by(email="company@careerbridge.local")
        )
        if company_user is not None:
            company_user.email = "company@careerbridge.com"
    if company_user is None:
        company_user = User(
            name="CareerBridge Demo Company",
            email="company@careerbridge.com",
            role="company",
        )
        company_user.set_password("Company@12345")
        db.session.add(company_user)
        db.session.flush()

    company = db.session.scalar(
        db.select(Company).filter_by(corporate_id="24ABCDE1234F1Z5")
    )
    if company is None:
        company = db.session.scalar(
            db.select(Company).filter_by(name="CareerBridge Demo Technologies")
        )
    if company is None:
        company = Company(
            user_id=company_user.id,
            name="CareerBridge Demo Technologies",
            website="https://example.com",
            rep_designation="HR Manager",
            corporate_id_type="GST",
            corporate_id="24ABCDE1234F1Z5",
            business_type="Private Limited",
            address="Science City Road, Ahmedabad",
            city="Ahmedabad",
            phone="9876543210",
            industry="Information Technology",
            company_size="51-200 employees",
            founded_year=2022,
            description="A demo technology company for testing hiring, company profiles and job posting.",
            rating=4.5,
            benefits=["Health insurance", "Remote work", "Learning budget"],
            is_approved=True,
            trust_score=90,
            documents={},
        )
        db.session.add(company)
    else:
        company.user_id = company_user.id

    db.session.commit()
    print("Demo admin and company accounts are ready.")

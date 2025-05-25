from sqlmodel import SQLModel, create_engine, Session, text
from app.config.config import get_settings

# Import all models to ensure they are registered with SQLModel
from app.domains.submissions.submissions_models import Submission

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300  # Recreate connections after 5 minutes
)


def create_db_and_tables():
    """Drop and recreate all database tables to ensure full sync with entities"""
    # Uncomment the following line to drop all tables and recreate them
    # with Session(engine) as session:
    #     session.exec(text("DROP SCHEMA public CASCADE"))
    #     session.exec(text("CREATE SCHEMA public"))
    #     session.exec(text("GRANT ALL ON SCHEMA public TO postgres"))
    #     session.exec(text("GRANT ALL ON SCHEMA public TO public"))
    #     session.commit()

    # Create all tables from scratch
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session

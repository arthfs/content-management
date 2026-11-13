from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_columns(eng=None):
    """Add columns introduced after a table was first created (create_all never alters tables)."""
    eng = eng or engine
    insp = inspect(eng)
    wanted = {
        "videos": {
            "file_path": "VARCHAR(255) NULL",
            "publish_options": "JSON NULL",
            "publish_status": "VARCHAR(40) NULL",
            "fail_reason": "VARCHAR(255) NULL",
        },
        "users": {
            "tiktok_refresh_token": "VARCHAR(512) NULL",
            "tiktok_token_expires_at": "TIMESTAMP WITH TIME ZONE NULL",
        },
    }
    tables = insp.get_table_names()
    for table, cols in wanted.items():
        if table not in tables:
            continue
        have = {c["name"] for c in insp.get_columns(table)}
        for name, ddl in cols.items():
            if name not in have:
                with eng.begin() as conn:
                    conn.execute(
                        text(
                            f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{name}" {ddl}'
                        )
                    )

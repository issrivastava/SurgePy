from app.database import engine
from app.models import Base  # ← Base must come from models

# IMPORTANT: import models so SQLAlchemy registers tables
import app.models

Base.metadata.create_all(bind=engine)

import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///church_lyft.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtdev")
    CHURCH_LAT = float(os.getenv("CHURCH_LAT", "45.4042"))
    CHURCH_LON = float(os.getenv("CHURCH_LON", "-71.8929"))
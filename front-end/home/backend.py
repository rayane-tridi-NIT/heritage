from fastapi import FastAPI, Query, HTTPException, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import jwt
import os
import uvicorn
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Expanded CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic models for API
class LocationBase(BaseModel):
    id: int
    title: str
    city: str
    category: str
    image_path: str
    
    class Config:
        orm_mode = True

# Database configuration and models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    role = Column(String(20), default="user")  # 'admin', 'guide', or 'user'
    profile_pic_path = Column(String(255), nullable=True)

# Add this after the User class definition
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    content = Column(String(1000))
    image_path = Column(String(255))
    user_id = Column(Integer)
    created_at = Column(String(100))

# Database configuration
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:ziyed@localhost/heritage_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create database tables
Base.metadata.create_all(bind=engine)

# Add after database configuration
def migrate_database():
    try:
        with engine.connect() as connection:
            # Add role column if it doesn't exist
            connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'")
            # Add profile_pic_path column if it doesn't exist
            connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_pic_path VARCHAR(255)")
            # Update existing users
            connection.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
            
            # Create posts table if it doesn't exist
            connection.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(100),
                    content VARCHAR(1000),
                    image_path VARCHAR(255),
                    user_id INT,
                    created_at VARCHAR(100)
                )
            """)
        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")

# Security configuration
SECRET_KEY = "03f105dfd55e50b021477c2dceed88e2c05f8cdccbd39480351a5e0746a63ffb"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"status": "ok", "message": "API is working"}

@app.get("/api/locations/", response_model=List[LocationBase])
async def get_locations(category: Optional[str] = Query(None)):
    try:
        logger.debug(f"Received request for locations with category: {category}")
        
        # Create a connection to execute the query
        with engine.connect() as connection:
            # First, let's debug what's in the table
            count_result = connection.execute("SELECT COUNT(*) FROM locations")
            total_count = count_result.scalar()
            logger.debug(f"Total locations in database: {total_count}")

            if category:
                categories = category.split(',')
                # Build query for filtered results
                placeholders = ', '.join(['%s' for _ in categories])
                query = f"SELECT * FROM locations WHERE category IN ({placeholders})"
                logger.debug(f"Executing query: {query} with parameters: {categories}")
                result = connection.execute(query, categories)
            else:
                # Get all locations with explicit column selection
                query = "SELECT id, title, city, category, image_path FROM locations"
                logger.debug(f"Executing query: {query}")
                result = connection.execute(query)

            # Fetch all rows and log them
            rows = result.fetchall()
            logger.debug(f"Raw database results: {rows}")
            
            # Convert results to list of LocationBase objects
            locations = []
            for row in rows:
                try:
                    location = LocationBase(
                        id=row[0],
                        title=row[1],
                        city=row[2],
                        category=row[3],
                        image_path=row[4]
                    )
                    locations.append(location)
                except Exception as e:
                    logger.error(f"Error converting row to LocationBase: {row}")
                    logger.error(f"Conversion error: {str(e)}")
            
            logger.debug(f"Converted to {len(locations)} LocationBase objects")
            return locations
            
    except Exception as e:
        logger.error(f"Error in get_locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/locations/")
async def debug_locations():
    """Debug endpoint to check all available locations"""
    try:
        with engine.connect() as connection:
            # Get total count
            count_result = connection.execute("SELECT COUNT(*) FROM locations")
            total_count = count_result.scalar()
            
            # Get all columns and rows
            result = connection.execute("SELECT * FROM locations")
            columns = result.keys()
            rows = result.fetchall()
            
            # Convert to list of dictionaries for better debugging
            locations = [dict(zip(columns, row)) for row in rows]
            
            return {
                "total_locations": total_count,
                "columns": list(columns),
                "locations": locations
            }
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str

    @classmethod
    def as_form(
        cls,
        full_name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
    ):
        return cls(full_name=full_name, email=email, password=password)

class UserLogin(BaseModel):
    email: str
    password: str

# Update the registration endpoint
@app.post("/register")
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Always create new user with 'user' role
        db_user = User(
            full_name=full_name,
            email=email,
            hashed_password=get_password_hash(password),
            role="user"  # Force role to be 'user'
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return {"message": "User created successfully", "status": "success"}
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/token")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.email == username).first()
        if not user:
            raise HTTPException(status_code=400, detail="Email not found")
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        access_token = create_access_token(data={
            "sub": user.email,
            "role": user.role,
            "full_name": user.full_name
        })
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "status": "success",
            "role": user.role
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Add new endpoint to get user profile
@app.get("/api/profile")
async def get_profile(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        # Decode token with error handling
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "profile_pic_path": user.profile_pic_path
        }
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Add this near the top of the file
UPLOAD_DIR = "static/profile_pics"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Add this after your existing endpoints
@app.post("/api/update-profile-pic")
async def update_profile_pic(
    picture_url: str = Form(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.email == payload["sub"]).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update database with picture URL/path
        user.profile_pic_path = picture_url
        db.commit()
        
        return {
            "message": "Profile picture updated successfully",
            "path": picture_url
        }
    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )

# Add this near other constants at the top
POST_UPLOAD_DIR = "static/post_images"
if not os.path.exists(POST_UPLOAD_DIR):
    os.makedirs(POST_UPLOAD_DIR)

# Update this endpoint
@app.post("/api/posts/create")
async def create_post(
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Verify user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.email == payload["sub"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Save image with proper path handling
        file_extension = image.filename.split(".")[-1]
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user.id}.{file_extension}"
        relative_path = f"static/post_images/{file_name}"  # Path for database
        absolute_path = os.path.join(POST_UPLOAD_DIR, file_name)  # Path for file saving
        
        try:
            with open(absolute_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save image")

        # Insert into locations table with relative path
        try:
            with engine.connect() as connection:
                result = connection.execute("SELECT MAX(id) FROM locations")
                max_id = result.fetchone()[0]
                new_id = 1 if max_id is None else max_id + 1
                
                connection.execute(
                    """
                    INSERT INTO locations (id, title, city, category, image_path) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (new_id, title, city, category, relative_path)
                )
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to insert location")
        
        return {
            "message": "Location created successfully", 
            "location_id": new_id,
            "image_path": relative_path
        }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Location creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Add new endpoint for token refresh after the login endpoint
@app.post("/api/refresh-token")
async def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create new token
        new_token = create_access_token(data={
            "sub": user.email,
            "role": user.role,
            "full_name": user.full_name
        })
        
        return {
            "access_token": new_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not refresh token")

# Update the main block to run migration
if __name__ == "__main__":
    logger.info("Starting server...")
    logger.info("Running database migrations...")
    migrate_database()
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")

from fastapi import (  # type: ignore
    FastAPI,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form
)
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from typing import List
import models
import schemas
import auth
import s3_service
from database import engine, get_db


# Create database tables
models.Base.metadata.create_all(bind=engine)


# Initialize FasAPI App
app = FastAPI(
    title="Media Upload Platform",
    description="Upload images & videos to AWS S3 with FastAPI + RDS",
    version="1.0.0"
)
# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methids=["*"],
    allow_headers=["*"],
)

# ========================================
# ROOT & HEALTH CHECK
# ========================================


@app.get("/")
def root():
    return {
        "messaged": "Media upaload from api",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "Healthy"}


# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) |
        (models.User.username == user.username)
    ).first()

    if existing_user:
        return HTTPException(
            status_code=400, detail="Email or username already registered"
        )
    # Create new user
    db_user = models.User(
        email=user.email,
        username=user.username,
        hash_password=auth.hash_password(user.password),
        full_name=user.full_name
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/auth/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""

    # Find user
    db_user = db.query(models.User).filter
    (models.User.username == user.username).first()

    if not db_user or not auth.verify_password(
        user.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    # Create token
    access_token = auth.create_access_token(data={"sub": db_user.id})
    return {"access token": access_token, "tokey type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Get current user info"""
    return current_user
# ========================================
# MEDIA UPLOAD ROUTES
# ========================================


@app.post(
    "/posts/upload-image",
    response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED
)
async def upload_image(
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an image"""

    # Upload to S3
    s3_url, file_size = s3_service.upload_to_s3(file, current_user.id, "image")

    # Create post in database
    db_post = models.Post(
        title=title,
        description=description,
        media_url=s3_url,
        media_type=models.MediaType.IMAGE,
        file_size=file_size,
        owner_id=current_user.id
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    # Add owner username for response
    response = schemas.PostResponse(
        **db_post.__dict__,
        owner_username=current_user.username
    )

    return response


@app.post(
    "/posts/upload-video",
    response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED
)
async def upload_video(
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a video"""

    # Upload to S3
    s3_url, file_size = s3_service.upload_to_s3(file, current_user.id, "video")

    # Create post in database
    db_post = models.Post(
        title=title,
        description=description,
        media_url=s3_url,
        media_type=models.MediaType.VIDEO,
        file_size=file_size,
        owner_id=current_user.id
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    response = schemas.PostResponse(
        **db_post.__dict__,
        owner_username=current_user.username
    )

    return response

# ========================================
# POST CRUD ROUTES
# ========================================


@app.get(
    "/posts",
    response_model=List[schemas.PostResponse]
)
def get_all_posts(
    skip: int = 0,
    limit: int = 20, db: Session = Depends(get_db)
):
    """Get all posts (paginated)"""

    posts = db.query(models.Post).offset(skip).limit(limit).all()

    # Add owner username to each post
    response = []
    for post in posts:
        response.append(schemas.PostResponse(
            **post.__dict__,
            owner_username=post.owner.username
        ))

    return response


@app.get("/posts/{post_id}", response_model=schemas.PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a single post"""

    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return schemas.PostResponse(
        **post.__dict__,
        owner_username=post.owner.username
    )


@app.get(
    "/users/{username}/posts",
    response_model=List[schemas.PostResponse]
)
def get_user_posts(username: str, db: Session = Depends(get_db)):
    """Get all posts by a specific user"""

    user = db.query(models.User).filter(
        models.User.username == username
        ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = db.query(models.Post).filter(models.Post.owner_id == user.id).all()

    response = []
    for post in posts:
        response.append(schemas.PostResponse(
            **post.__dict__,
            owner_username=user.username
        ))

    return response


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post (only owner can delete)"""

    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this post"
        )

    # Delete from S3
    s3_service.delete_from_s3(post.media_url)

    # Delete from database
    db.delete(post)
    db.commit()

    return None

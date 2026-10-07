import uvicorn
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware




try:
    from .database import engine, Base, get_db
    from . import models, schemas, crud
except ImportError:
    from database import engine, Base, get_db
    import models, schemas, crud


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Agrova Farm Data API",
    description="FastAPI backend for storing and retrieving farm records used by the Agrova AI chatbot.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Agrova Farm Data API",
        "docs_url": "/docs",
        "chat_ui": "/ui/",
        "version": "0.1.0"
    }

# Simple chat test page (chat_ui/index.html), served at http://localhost:8000/ui/
# (The team's Next.js app lives in frontend/ and is run separately with npm.)
CHAT_UI_DIR = Path(__file__).resolve().parent.parent / "chat_ui"
if CHAT_UI_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(CHAT_UI_DIR), html=True), name="ui")

# ------------------- Animal Endpoints -------------------

@app.post("/animals/", response_model=schemas.AnimalRead, status_code=status.HTTP_201_CREATED)
async def create_animal(animal: schemas.AnimalCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_animal(db, animal)

@app.get("/animals/{animal_id}", response_model=schemas.AnimalRead)
async def read_animal(animal_id: int, db: AsyncSession = Depends(get_db)):
    db_animal = await crud.get_animal(db, animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return db_animal

@app.get("/animals/", response_model=List[schemas.AnimalRead])
async def list_animals(farmer_id: int = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.list_animals(db, farmer_id=farmer_id, skip=skip, limit=limit)

# ------------------- HealthEvent Endpoints -------------------
@app.post("/health-events/", response_model=schemas.HealthEventRead, status_code=status.HTTP_201_CREATED)
async def create_health_event(event: schemas.HealthEventCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_health_event(db, event)

@app.get("/health-events/", response_model=List[schemas.HealthEventRead])
async def list_health_events(animal_id: int = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.list_health_events(db, animal_id=animal_id, skip=skip, limit=limit)

# ------------------- FeedRecord Endpoints -------------------
@app.post("/feed-records/", response_model=schemas.FeedRecordRead, status_code=status.HTTP_201_CREATED)
async def create_feed_record(feed: schemas.FeedRecordCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_feed_record(db, feed)

@app.get("/feed-records/", response_model=List[schemas.FeedRecordRead])
async def list_feed_records(animal_id: int = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.list_feed_records(db, animal_id=animal_id, skip=skip, limit=limit)

# ------------------- ProductionRecord Endpoints -------------------
@app.post("/production-records/", response_model=schemas.ProductionRecordRead, status_code=status.HTTP_201_CREATED)
async def create_production_record(prod: schemas.ProductionRecordCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_production_record(db, prod)

@app.get("/production-records/", response_model=List[schemas.ProductionRecordRead])
async def list_production_records(animal_id: int = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.list_production_records(db, animal_id=animal_id, skip=skip, limit=limit)

# ------------------- AI Chatbot / Assistant Endpoint -------------------
class ChatMessageIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    farmer_id: int = 1

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        return v

    session_id: Optional[str] = "default"
    history: Optional[List[Dict[str, str]]] = None

@app.post("/chat/")
async def chat_with_agrova(chat_in: ChatMessageIn):
    """
    Main Agrova Multi-Turn Conversational Endpoint:
    Processes farmer input (English/Pidgin), remembers prior conversation turns,
    queries RAG documents & Farm DB, and returns structured AI response.
    """
    try:
        from chatbot.chatbot import agrova_chat
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).resolve().parent.parent))
        from chatbot.chatbot import agrova_chat
    
    result = agrova_chat(
        chat_in.message, 
        farmer_id=chat_in.farmer_id,
        session_id=chat_in.session_id or "default",
        history=chat_in.history
    )
    return {
        "status": "success",
        "user_message": chat_in.message,
        "farmer_id": chat_in.farmer_id,
        "session_id": result["session_id"],
        "reply": result["reply"],
        "history": result["history"]
    }


if __name__ == "__main__":
    # Run with: python -m backend.main
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


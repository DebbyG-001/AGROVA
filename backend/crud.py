from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
try:
    from . import models, schemas
except ImportError:
    import models, schemas


# ------------------- Animal CRUD -------------------
async def create_animal(db: AsyncSession, animal_in: schemas.AnimalCreate):
    db_animal = models.Animal(**animal_in.model_dump())
    db.add(db_animal)
    await db.commit()
    await db.refresh(db_animal)
    return db_animal

async def get_animal(db: AsyncSession, animal_id: int):
    result = await db.execute(select(models.Animal).where(models.Animal.id == animal_id))
    return result.scalars().first()

async def list_animals(db: AsyncSession, farmer_id: int = None, skip: int = 0, limit: int = 100):
    stmt = select(models.Animal)
    if farmer_id is not None:
        stmt = stmt.where(models.Animal.farmer_id == farmer_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# ------------------- HealthEvent CRUD -------------------
async def create_health_event(db: AsyncSession, event_in: schemas.HealthEventCreate):
    db_event = models.HealthEvent(**event_in.model_dump())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

async def list_health_events(db: AsyncSession, animal_id: int = None, skip: int = 0, limit: int = 100):
    stmt = select(models.HealthEvent)
    if animal_id is not None:
        stmt = stmt.where(models.HealthEvent.animal_id == animal_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# ------------------- FeedRecord CRUD -------------------
async def create_feed_record(db: AsyncSession, feed_in: schemas.FeedRecordCreate):
    db_feed = models.FeedRecord(**feed_in.model_dump())
    db.add(db_feed)
    await db.commit()
    await db.refresh(db_feed)
    return db_feed

async def list_feed_records(db: AsyncSession, animal_id: int = None, skip: int = 0, limit: int = 100):
    stmt = select(models.FeedRecord)
    if animal_id is not None:
        stmt = stmt.where(models.FeedRecord.animal_id == animal_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# ------------------- ProductionRecord CRUD -------------------
async def create_production_record(db: AsyncSession, prod_in: schemas.ProductionRecordCreate):
    db_prod = models.ProductionRecord(**prod_in.model_dump())
    db.add(db_prod)
    await db.commit()
    await db.refresh(db_prod)
    return db_prod

async def list_production_records(db: AsyncSession, animal_id: int = None, skip: int = 0, limit: int = 100):
    stmt = select(models.ProductionRecord)
    if animal_id is not None:
        stmt = stmt.where(models.ProductionRecord.animal_id == animal_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


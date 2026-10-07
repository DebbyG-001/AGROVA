from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
import datetime

class AnimalBase(BaseModel):
    farmer_id: int = Field(..., description="ID of the farmer owning the animal")
    species: str = Field(..., description="Species of the animal, e.g., poultry, cattle")
    breed: Optional[str] = Field(None, description="Breed of the animal")
    age_days: Optional[int] = Field(None, description="Age in days")
    batch: Optional[str] = Field(None, description="Batch identifier for groups of animals")
    purchase_date: Optional[datetime.date] = Field(None, description="Date the animal was purchased")
    notes: Optional[str] = Field(None, description="Additional free‑form notes")

class AnimalCreate(AnimalBase):
    pass

class AnimalRead(AnimalBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class HealthEventBase(BaseModel):
    animal_id: int = Field(..., description="Related animal ID")
    date: datetime.date = Field(..., description="Date of the health event")
    symptom: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

class HealthEventCreate(HealthEventBase):
    pass

class HealthEventRead(HealthEventBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class FeedRecordBase(BaseModel):
    animal_id: int
    date: datetime.date
    feed_type: Optional[str] = None
    quantity_kg: Optional[float] = None
    cost: Optional[float] = None
    notes: Optional[str] = None

class FeedRecordCreate(FeedRecordBase):
    pass

class FeedRecordRead(FeedRecordBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ProductionRecordBase(BaseModel):
    animal_id: int
    date: datetime.date
    metric: str = Field(..., description="Metric type, e.g., 'eggs', 'milk_liters', 'weight_kg'")
    amount: float = Field(..., description="Quantity for the metric")
    notes: Optional[str] = None

class ProductionRecordCreate(ProductionRecordBase):
    pass

class ProductionRecordRead(ProductionRecordBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Aggregate view for a farmer (optional helper)
class FarmSummary(BaseModel):
    farmer_id: int
    animal_count: int
    health_event_count: int
    feed_record_count: int
    production_record_count: int
    model_config = ConfigDict(from_attributes=True)



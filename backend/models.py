from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
try:
    from .database import Base
except ImportError:
    from database import Base

import enum

class SpeciesEnum(str, enum.Enum):
    poultry = "poultry"
    cattle = "cattle"
    goat = "goat"
    sheep = "sheep"
    pig = "pig"
    fish = "fish"
    other = "other"

class Animal(Base):
    __tablename__ = "animals"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, index=True)  # could link to a users table later
    species = Column(Enum(SpeciesEnum), nullable=False)
    breed = Column(String, nullable=True)
    age_days = Column(Integer, nullable=True)
    batch = Column(String, nullable=True)
    purchase_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    health_events = relationship("HealthEvent", back_populates="animal", cascade="all, delete-orphan")
    feed_records = relationship("FeedRecord", back_populates="animal", cascade="all, delete-orphan")
    production_records = relationship("ProductionRecord", back_populates="animal", cascade="all, delete-orphan")

class HealthEvent(Base):
    __tablename__ = "health_events"
    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    date = Column(Date, nullable=False)
    symptom = Column(String, nullable=True)
    diagnosis = Column(String, nullable=True)
    treatment = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    animal = relationship("Animal", back_populates="health_events")

class FeedRecord(Base):
    __tablename__ = "feed_records"
    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    date = Column(Date, nullable=False)
    feed_type = Column(String, nullable=True)
    quantity_kg = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    animal = relationship("Animal", back_populates="feed_records")

class ProductionRecord(Base):
    __tablename__ = "production_records"
    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    date = Column(Date, nullable=False)
    # For poultry: eggs, for cattle: milk_liters, for fish: weight_kg, etc.
    metric = Column(String, nullable=False)  # e.g., "eggs", "milk_liters"
    amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    animal = relationship("Animal", back_populates="production_records")

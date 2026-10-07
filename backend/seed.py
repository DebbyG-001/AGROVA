import asyncio
import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .database import AsyncSessionLocal, engine, Base
    from .models import Animal, HealthEvent, FeedRecord, ProductionRecord, SpeciesEnum
except ImportError:
    from database import AsyncSessionLocal, engine, Base
    from models import Animal, HealthEvent, FeedRecord, ProductionRecord, SpeciesEnum

# NOTE: all records below are DEMO data (quantities and prices are illustrative, not real farm data).
# The script is safe to run more than once: an animal is only created if no animal with the same
# farmer_id + batch exists, and records are only added to animals that have none of that type yet.

FARMER_ID = 1  # Farmer Musa


def build_seed_plan(today: datetime.date):
    def d(days_ago: int) -> datetime.date:
        return today - datetime.timedelta(days=days_ago)

    return [
        # ------------------------------------------------------------------ Poultry
        {
            "animal": dict(
                species=SpeciesEnum.poultry, breed="Ross 308 Broiler", age_days=28,
                batch="Batch B17 (500 birds)", purchase_date=d(28),
                notes="Purchased from Zartech hatchery, currently in grower stage."),
            "health": [
                # Recent issue matching the farmer's pidgin statement
                dict(date=d(1), symptom="Watery stool / diarrhea, reduced feed intake noticed in ~15 birds",
                     diagnosis=None, treatment="Increased clean water, awaiting vet assessment",
                     notes="Farmer observed birds clustering and low appetite."),
                dict(date=d(14), symptom="Routine Vaccination", diagnosis="Healthy",
                     treatment="Gumboro (IBD) 2nd dose administered in drinking water",
                     notes="Vaccination successful with minimal stress."),
            ],
            "feed": [
                dict(date=d(2), feed_type="Broiler Grower Pellets", quantity_kg=48.0, cost=22000.0,
                     notes="Normal feeding rate."),
                dict(date=d(1), feed_type="Broiler Grower Pellets", quantity_kg=32.0, cost=22000.0,
                     notes="Noticeable drop in feed consumption (16kg unconsumed)."),
            ],
            "production": [],
        },
        {
            "animal": dict(
                species=SpeciesEnum.poultry, breed="Isa Brown Layers", age_days=180,
                batch="Batch L03 (200 layers)", purchase_date=d(180),
                notes="Point of lay birds in battery cage system."),
            "health": [
                dict(date=d(20), symptom="Routine Deworming", diagnosis="Healthy",
                     treatment="Piperazine dewormer given in water", notes="Pre-peak production maintenance."),
            ],
            "feed": [
                dict(date=d(1), feed_type="Layers Mash (16.5% CP)", quantity_kg=24.0, cost=11500.0,
                     notes="Morning and afternoon feeding."),
            ],
            "production": [
                dict(date=d(4), metric="eggs", amount=175.0, notes="Good shell quality"),
                dict(date=d(3), metric="eggs", amount=172.0, notes="Normal production"),
                dict(date=d(2), metric="eggs", amount=160.0, notes="Slight decrease"),
                dict(date=d(1), metric="eggs", amount=145.0, notes="Hot afternoon stress noted"),
                dict(date=d(0), metric="eggs", amount=138.0, notes="Egg count drop continuing"),
            ],
        },
        # ------------------------------------------------------------------ Goats
        {
            "animal": dict(
                species=SpeciesEnum.goat, breed="West African Dwarf", age_days=365,
                batch="Herd G1 (15 goats)", purchase_date=d(365),
                notes="Semi-intensive grazing system."),
            "health": [
                dict(date=d(90), symptom="Routine PPR vaccination", diagnosis="Healthy",
                     treatment="Whole herd vaccinated against PPR by the agro-vet", notes="No reactions."),
                dict(date=d(2), symptom="Cough and runny nose in 2 kids, loose stool in one",
                     diagnosis=None, treatment="Isolated the 2 kids in a separate pen",
                     notes="Other goats look normal so far. Rainy season, pen is damp."),
            ],
            "feed": [
                dict(date=d(1), feed_type="Cassava peels + Leucaena browse (cut and carry)", quantity_kg=20.0,
                     cost=1500.0, notes="Plus a handful of concentrate for the 2 pregnant does."),
            ],
            "production": [],
        },
        # ------------------------------------------------------------------ Sheep
        {
            "animal": dict(
                species=SpeciesEnum.sheep, breed="Yankasa", age_days=540,
                batch="Flock Y1 (12 Yankasa sheep)", purchase_date=d(540),
                notes="Stall-fed fattening rams and ewes, average about 35 kg."),
            "health": [
                dict(date=d(75), symptom="Routine PPR vaccination", diagnosis="Healthy",
                     treatment="Flock vaccinated against PPR", notes="Vet visit, no problems."),
            ],
            "feed": [
                dict(date=d(1), feed_type="Digitaria hay + concentrate (about 2% of body weight)", quantity_kg=8.4,
                     cost=4200.0, notes="Concentrate portion for 12 sheep; hay fed freely."),
            ],
            "production": [],
        },
        # ------------------------------------------------------------------ Cattle
        {
            "animal": dict(
                species=SpeciesEnum.cattle, breed="Bunaji (White Fulani)", age_days=1800,
                batch="Herd C1 (8 Bunaji: 5 cows, 3 calves)", purchase_date=d(1800),
                notes="Agropastoral grazing, dry-season cottonseed cake supplement. Milk is for the household."),
            "health": [
                dict(date=d(120), symptom="Routine FMD vaccination", diagnosis="Healthy",
                     treatment="Herd vaccinated by the state vet team", notes="Cold chain was kept."),
                dict(date=d(3), symptom="Fever, watery eyes and firm skin lumps (about 2 to 5 cm) on 2 cows",
                     diagnosis=None, treatment="Separated the 2 cows; sprayed against flies",
                     notes="Lumps appeared after heavy rain with many biting flies. Milk dropping."),
            ],
            "feed": [
                dict(date=d(1), feed_type="Cottonseed cake (supplement) + natural pasture", quantity_kg=6.0,
                     cost=3600.0, notes="Dry-season supplement for the lactating cows."),
            ],
            "production": [
                dict(date=d(4), metric="milk_liters", amount=2.6, notes="Total milk taken for household"),
                dict(date=d(3), metric="milk_liters", amount=2.5, notes=None),
                dict(date=d(2), metric="milk_liters", amount=2.3, notes="Lumps noticed on 2 cows"),
                dict(date=d(1), metric="milk_liters", amount=2.0, notes=None),
                dict(date=d(0), metric="milk_liters", amount=1.8, notes="Milk still dropping"),
            ],
        },
        # ------------------------------------------------------------------ Pigs
        {
            "animal": dict(
                species=SpeciesEnum.pig, breed="Large White x local", age_days=24,
                batch="Sow S1 and 9 piglets", purchase_date=None,
                notes="Concrete-floor farrowing pen. Weaning planned at about 8 weeks. Piglets 24 days old."),
            "health": [
                dict(date=d(24), symptom="Farrowing", diagnosis="Healthy",
                     treatment="None needed", notes="10 piglets born, 9 alive, sow doing well."),
                dict(date=d(2), symptom="4 of the 9 piglets look pale and are growing slower",
                     diagnosis=None, treatment="None yet",
                     notes="No iron injection given and no soil in the pen. No diarrhoea, no fever."),
            ],
            "feed": [
                dict(date=d(1), feed_type="Lactating sow meal (20% protein)", quantity_kg=4.5, cost=4000.0,
                     notes="Sow fed twice daily; piglets only nibble sow feed."),
            ],
            "production": [
                dict(date=d(14), metric="litter_weight_kg", amount=22.0, notes="Total weight of 9 piglets"),
                dict(date=d(0), metric="litter_weight_kg", amount=39.5, notes="4 piglets lagging behind the rest"),
            ],
        },
        # ------------------------------------------------------------------ Fish
        {
            "animal": dict(
                species=SpeciesEnum.fish, breed="African catfish (Clarias gariepinus)", age_days=75,
                batch="Pond C1 (2,000 catfish)", purchase_date=d(75),
                notes="Earthen pond about 400 m2 (5 fish per m2), 35% protein pellets twice daily, no aeration."),
            "health": [
                dict(date=d(1), symptom="Fish gasping at the surface at dawn, pond water very green; 12 dead found",
                     diagnosis=None, treatment="Skipped the morning feeding and added some fresh water",
                     notes="Weather was hot and cloudy for 2 days."),
            ],
            "feed": [
                dict(date=d(3), feed_type="Catfish pellets 35% protein", quantity_kg=4.8, cost=9600.0,
                     notes="Normal feeding."),
                dict(date=d(1), feed_type="Catfish pellets 35% protein", quantity_kg=2.4, cost=4800.0,
                     notes="Feed halved after fish gasped at the surface."),
            ],
            "production": [
                dict(date=d(14), metric="avg_weight_g", amount=52.0, notes="Cast-net sample of 30 fish"),
                dict(date=d(0), metric="avg_weight_g", amount=85.0, notes="Cast-net sample of 30 fish"),
            ],
        },
        {
            "animal": dict(
                species=SpeciesEnum.fish, breed="Nile tilapia", age_days=110,
                batch="Pond T1 (1,200 tilapia)", purchase_date=d(110),
                notes="Earthen pond about 600 m2 (2 fish per m2), fertilised with poultry manure plus pellets."),
            "health": [
                dict(date=d(5), symptom="Some fish scratching against the pond wall, white spots on the skin",
                     diagnosis=None, treatment="None yet", notes="Water is clear, appetite is still good."),
            ],
            "feed": [
                dict(date=d(1), feed_type="Floating tilapia pellets 30% protein", quantity_kg=3.5, cost=7000.0,
                     notes="Fed to about half of what the fish would eat."),
            ],
            "production": [
                dict(date=d(14), metric="avg_weight_g", amount=140.0, notes="Cast-net sample"),
                dict(date=d(0), metric="avg_weight_g", amount=172.0, notes="Cast-net sample"),
            ],
        },
    ]


async def get_or_create_animal(session: AsyncSession, fields: dict):
    result = await session.execute(
        select(Animal).where(Animal.farmer_id == FARMER_ID, Animal.batch == fields["batch"])
    )
    animal = result.scalars().first()
    if animal:
        return animal, False
    animal = Animal(farmer_id=FARMER_ID, **fields)
    session.add(animal)
    await session.flush()  # populate ID
    return animal, True


async def add_records_if_empty(session: AsyncSession, model, animal: Animal, rows: list) -> int:
    count = (await session.execute(
        select(func.count()).select_from(model).where(model.animal_id == animal.id)
    )).scalar_one()
    if count or not rows:
        return 0
    session.add_all([model(animal_id=animal.id, **row) for row in rows])
    return len(rows)


async def seed_database():
    print("Starting Agrova Database Seeding (safe to re-run)...")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        plan = build_seed_plan(datetime.date.today())
        created = 0
        added = {"health": 0, "feed": 0, "production": 0}

        for item in plan:
            animal, is_new = await get_or_create_animal(session, item["animal"])
            created += int(is_new)
            added["health"] += await add_records_if_empty(session, HealthEvent, animal, item["health"])
            added["feed"] += await add_records_if_empty(session, FeedRecord, animal, item["feed"])
            added["production"] += await add_records_if_empty(session, ProductionRecord, animal, item["production"])
            print(f"  {'NEW ' if is_new else 'have'}  {animal.batch}  (id {animal.id}, {animal.species.value})")

        await session.commit()

    print(f"Done. New animals: {created}. New records: "
          f"{added['health']} health, {added['feed']} feed, {added['production']} production.")


if __name__ == "__main__":
    asyncio.run(seed_database())

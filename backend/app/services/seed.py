from sqlalchemy.orm import Session

from app.models.filament import FilamentType, Manufacturer
from app.models.settings import AppSettings

DEFAULT_FILAMENT_TYPES = [
    {"name": "PLA", "abbreviation": "PLA", "description": "Most popular, easy to print, biodegradable"},
    {"name": "PLA+", "abbreviation": "PLA+", "description": "Enhanced PLA with better strength and flexibility"},
    {"name": "PETG", "abbreviation": "PETG", "description": "Strong, flexible, food-safe, good chemical resistance"},
    {"name": "ABS", "abbreviation": "ABS", "description": "Strong, heat-resistant, requires enclosure"},
    {"name": "ASA", "abbreviation": "ASA", "description": "UV-resistant ABS alternative, great for outdoor use"},
    {"name": "TPU", "abbreviation": "TPU", "description": "Flexible/elastic filament for soft parts"},
    {"name": "Nylon", "abbreviation": "NYLON", "description": "Very strong, flexible, hygroscopic"},
    {"name": "PC", "abbreviation": "PC", "description": "Polycarbonate - extremely strong, heat-resistant"},
    {"name": "HIPS", "abbreviation": "HIPS", "description": "Support material for ABS, dissolves in limonene"},
    {"name": "PVA", "abbreviation": "PVA", "description": "Water-soluble support material"},
    {"name": "Wood PLA", "abbreviation": "WOOD", "description": "PLA with wood fibers for wood-like finish"},
    {"name": "Carbon Fiber", "abbreviation": "CF", "description": "Reinforced filament with carbon fiber strands"},
    {"name": "Silk PLA", "abbreviation": "SILK", "description": "PLA with shiny, silky surface finish"},
]

DEFAULT_MANUFACTURERS = [
    {"name": "Hatchbox", "website": "https://www.hatchbox3d.com"},
    {"name": "eSun", "website": "https://www.esun3d.com"},
    {"name": "Prusament", "website": "https://www.prusa3d.com/category/prusament"},
    {"name": "Polymaker", "website": "https://www.polymaker.com"},
    {"name": "Overture", "website": "https://overture3d.com"},
    {"name": "Inland", "website": None},
    {"name": "Sunlu", "website": "https://www.sunlu.com"},
    {"name": "Bambu Lab", "website": "https://bambulab.com"},
    {"name": "Elegoo", "website": "https://www.elegoo.com"},
    {"name": "Creality", "website": "https://www.creality.com"},
    {"name": "3D Solutech", "website": "https://www.3dsolutech.com"},
    {"name": "MatterHackers", "website": "https://www.matterhackers.com"},
    {"name": "Proto-Pasta", "website": "https://www.proto-pasta.com"},
]


def seed_database(db: Session) -> None:
    """Seed default data if tables are empty."""
    # Seed filament types
    if db.query(FilamentType).count() == 0:
        for ft_data in DEFAULT_FILAMENT_TYPES:
            db.add(FilamentType(**ft_data, is_default=True))
        db.commit()

    # Seed manufacturers
    if db.query(Manufacturer).count() == 0:
        for mfg_data in DEFAULT_MANUFACTURERS:
            db.add(Manufacturer(**mfg_data, is_default=True))
        db.commit()

    # Seed settings singleton
    if db.query(AppSettings).count() == 0:
        db.add(AppSettings(id=1))
        db.commit()

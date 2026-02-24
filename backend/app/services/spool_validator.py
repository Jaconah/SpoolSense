"""Spool inventory validation service for Issue #17."""
from dataclasses import dataclass
from typing import List
from sqlalchemy.orm import Session, joinedload

from app.models.filament import Spool, FilamentType, Manufacturer
from app.models.settings import AppSettings


@dataclass
class SpoolShortage:
    """Details about a spool that would go negative."""
    spool_id: int
    tracking_id: str | None
    color_name: str
    filament_type_name: str
    manufacturer_name: str | None
    current_weight_g: float
    requested_weight_g: float
    resulting_weight_g: float
    shortage_g: float
    within_reserve: bool = False  # True = has enough but dips into the safety buffer


@dataclass
class SpoolValidationResult:
    """Result of spool inventory validation."""
    is_valid: bool
    shortages: List[SpoolShortage]

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.shortages) > 0


def validate_spool_inventory(
    db: Session,
    spool_usages: List[tuple[int, float]]  # [(spool_id, grams_to_use), ...]
) -> SpoolValidationResult:
    """
    Validate that spools have sufficient inventory for requested usage.

    Respects settings:
    - enable_spool_negative_prevention: If True, enforce hard blocking
    - minimum_spool_reserve_g: Reserve amount to keep (accounts for waste/purge)

    Args:
        db: Database session
        spool_usages: List of (spool_id, grams_to_use) tuples

    Returns:
        SpoolValidationResult with validation status and any shortages
    """
    # Load settings to get reserve and prevention toggle
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()

    # Default values if settings not found
    reserve_g = settings.minimum_spool_reserve_g if settings else 5.0
    prevention_enabled = settings.enable_spool_negative_prevention if settings else True

    # If prevention is disabled, skip validation entirely
    if not prevention_enabled:
        return SpoolValidationResult(is_valid=True, shortages=[])

    shortages = []

    for spool_id, grams_to_use in spool_usages:
        # Load spool with relationships for complete information
        spool = (
            db.query(Spool)
            .options(
                joinedload(Spool.filament_type),
                joinedload(Spool.manufacturer)
            )
            .filter(Spool.id == spool_id)
            .first()
        )

        if not spool:
            continue  # Spool not found - let normal validation handle this

        # Calculate usable weight (remaining - reserve)
        usable_weight = spool.remaining_weight_g - reserve_g
        resulting_weight = usable_weight - grams_to_use

        # Hard block if would go below reserve
        if resulting_weight < 0:
            shortages.append(SpoolShortage(
                spool_id=spool.id,
                tracking_id=spool.tracking_id,
                color_name=spool.color_name,
                filament_type_name=spool.filament_type.name,
                manufacturer_name=spool.manufacturer.name if spool.manufacturer else None,
                current_weight_g=spool.remaining_weight_g,
                requested_weight_g=grams_to_use,
                resulting_weight_g=spool.remaining_weight_g - grams_to_use,
                shortage_g=max(0.0, grams_to_use - spool.remaining_weight_g),
                within_reserve=spool.remaining_weight_g >= grams_to_use
            ))

    return SpoolValidationResult(
        is_valid=len(shortages) == 0,
        shortages=shortages
    )


def find_alternative_spools(
    db: Session,
    filament_type_id: int,
    minimum_grams: float,
    exclude_spool_ids: List[int] | None = None
) -> List[Spool]:
    """
    Find alternative spools with sufficient inventory.

    Respects settings:
    - minimum_spool_reserve_g: Ensures alternatives have enough + reserve

    Args:
        db: Database session
        filament_type_id: Filament type to match
        minimum_grams: Minimum grams required
        exclude_spool_ids: Spool IDs to exclude from results

    Returns:
        List of spools with sufficient inventory (up to 5)
    """
    # Load settings to get reserve
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    reserve_g = settings.minimum_spool_reserve_g if settings else 5.0

    # Find spools with enough inventory PLUS reserve
    query = db.query(Spool).filter(
        Spool.filament_type_id == filament_type_id,
        Spool.remaining_weight_g >= (minimum_grams + reserve_g),
        Spool.is_active == True
    )

    if exclude_spool_ids:
        query = query.filter(~Spool.id.in_(exclude_spool_ids))

    return query.order_by(Spool.remaining_weight_g.desc()).limit(5).all()

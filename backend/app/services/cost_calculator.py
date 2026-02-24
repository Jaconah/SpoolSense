from app.models.settings import AppSettings
from app.schemas.cost_estimate import CostBreakdown


def calculate_cost(
    grams: float,
    print_time_minutes: int,
    cost_per_kg: float,
    settings: AppSettings,
) -> CostBreakdown:
    filament_cost = (grams / 1000) * cost_per_kg
    electricity_cost = (
        (print_time_minutes / 60) * (settings.printer_wattage / 1000) * settings.electricity_rate_kwh
    )
    time_cost = (print_time_minutes / 60) * settings.hourly_rate
    depreciation_cost = (print_time_minutes / 60) * settings.machine_depreciation_rate
    fixed_fee = settings.fixed_fee_per_order
    subtotal = filament_cost + electricity_cost + time_cost + depreciation_cost + fixed_fee
    profit = subtotal * (settings.profit_margin_percent / 100)
    total = subtotal + profit

    return CostBreakdown(
        filament_cost=round(filament_cost, 2),
        electricity_cost=round(electricity_cost, 2),
        time_cost=round(time_cost, 2),
        depreciation_cost=round(depreciation_cost, 2),
        fixed_fee=round(fixed_fee, 2),
        subtotal=round(subtotal, 2),
        profit_margin_percent=settings.profit_margin_percent,
        profit=round(profit, 2),
        total=round(total, 2),
        currency_symbol=settings.currency_symbol,
    )

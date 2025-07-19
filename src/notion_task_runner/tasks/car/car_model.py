from dataclasses import dataclass


@dataclass
class Car:
    reg_number: str
    model: str
    model_year: int
    color: str
    inspected_at: str
    next_inspection_latest_at: str
    tax_yearly_sek: int
    registered_at: str
    mileage_km: int
    horsepower: int

    def __str__(self) -> str:
        return (
            f"Car {self.reg_number} ({self.model_year} {self.model}, {self.color})\n"
            f"  • Inspected: {self.inspected_at}\n"
            f"  • Next Inspection: {self.next_inspection_latest_at}\n"
            f"  • Tax: {self.tax_yearly_sek} SEK/year\n"
            f"  • Registered: {self.registered_at}\n"
            f"  • Mileage: {self.mileage_km:,} km\n"
            f"  • Horsepower: {self.horsepower} hp"
        )

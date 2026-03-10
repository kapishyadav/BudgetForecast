from enum import Enum

class ForecastType(Enum):
    """Enum for different forecast aggregation levels."""
    OVERALL_AGGREGATE = "overall_aggregate"
    ACCOUNT = "account"
    SERVICE = "service"
    BUCODE = "bu_code"
    SEGMENT = "segment"

    @classmethod
    def choices(cls):
        """Return choices tuple for Django forms or models."""
        return [(ft.value, ft.name.title()) for ft in cls]


class Granularity(Enum):
    """Enum for different forecast granularities."""
    MONTHLY = "monthly"
    DAILY = "daily"

    @classmethod
    def choices(cls):
        """Return choices tuple for Django forms or models."""
        return [(ft.value, ft.name.title()) for ft in cls]


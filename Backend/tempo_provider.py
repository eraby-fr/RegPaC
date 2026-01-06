import requests
import logging
from enum import Enum
from typing import Optional

LOGGER = logging.getLogger(__name__)


class DayPrice(Enum):
    UNKNOWN = 0
    LOW = 1  # Blue - Bleu
    NORMAL = 2  # White - Blanc
    HIGH = 3  # Red - Rouge


class TempoProvider:
    """
    Provider class to fetch Tempo day information from EDF API.
    Tempo is a French electricity pricing system with three colors:
    - Blue (Bleu): Low price
    - White (Blanc): Normal price
    - Red (Rouge): High price
    """

    BASE_URL = "https://www.api-couleur-tempo.fr/api/jourTempo"

    def __init__(self):
        self._today_price: DayPrice = DayPrice.UNKNOWN
        self._tomorrow_price: DayPrice = DayPrice.UNKNOWN
        self._today_data: Optional[dict] = None
        self._tomorrow_data: Optional[dict] = None

    def _map_code_to_price(self, code_day: int) -> DayPrice:
        if code_day == 1:
            return DayPrice.LOW
        elif code_day == 2:
            return DayPrice.NORMAL
        elif code_day == 3:
            return DayPrice.HIGH
        else:
            LOGGER.warning(f"Unknown Tempo codeJour: {code_day}")
            return DayPrice.UNKNOWN

    def _fetch_tempo_day(self, endpoint: str) -> Optional[dict]:
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            LOGGER.info(f"Fetching Tempo data from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            LOGGER.info(f"Successfully fetched {endpoint} Tempo data: {data}")
            return data
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Failed to fetch Tempo {endpoint} data: {e}")
            return None
        except ValueError as e:
            LOGGER.error(f"Failed to parse Tempo {endpoint} JSON response: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"Unexpected error fetching Tempo {endpoint} data: {e}")
            return None

    def update(self):
        LOGGER.info("Updating Tempo provider data...")

        # Fetch today's data
        today_data = self._fetch_tempo_day("today")
        if today_data:
            self._today_data = today_data
            self._today_price = self._map_code_to_price(today_data.get("codeJour", 0))
            LOGGER.info(f"Today's Tempo price: {self._today_price.name}")
        else:
            self._today_price = DayPrice.UNKNOWN
            LOGGER.warning("Failed to update today's Tempo price")

        tomorrow_data = self._fetch_tempo_day("tomorrow")
        if tomorrow_data:
            self._tomorrow_data = tomorrow_data
            self._tomorrow_price = self._map_code_to_price(tomorrow_data.get("codeJour", 0))
            LOGGER.info(f"Tomorrow's Tempo price: {self._tomorrow_price.name}")
        else:
            self._tomorrow_price = DayPrice.UNKNOWN
            LOGGER.warning("Failed to update tomorrow's Tempo price")

    def get_today_price(self) -> DayPrice:
        """Get today's electricity price level."""
        return self._today_price

    def get_tomorrow_price(self) -> DayPrice:
        """Get tomorrow's electricity price level."""
        return self._tomorrow_price

    def get_today_data(self) -> Optional[dict]:
        """Get raw today's Tempo data."""
        return self._today_data

    def get_tomorrow_data(self) -> Optional[dict]:
        """Get raw tomorrow's Tempo data."""
        return self._tomorrow_data

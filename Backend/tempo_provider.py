import requests
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

LOGGER = logging.getLogger(__name__)

# A Tempo day is not a calendar day : it runs from 06:00 to 06:00 the next
# morning. The API documents /jourTempo/today as "la couleur tarifaire valable
# de 6h du matin jusqu'a 6h demain matin".
TEMPO_DAY_START_HOUR = 6


class DayPrice(Enum):
    UNKNOWN = 0
    LOW = 1  # Blue - Bleu
    NORMAL = 2  # White - Blanc
    HIGH = 3  # Red - Rouge


class DayStatus(Enum):
    """Why a DayPrice holds the value it holds.

    DayPrice.UNKNOWN on its own is ambiguous : it used to mean "EDF has not
    published that day yet", "the API could not be reached" and "the value has
    been frozen for days" all at once, which made outages impossible to
    diagnose. The status tells those apart.
    """
    NEVER_FETCHED = 0  # no successful call since start-up
    OK = 1  # colour published and fetched
    NOT_PUBLISHED = 2  # API reached, EDF has not published that day yet
    FETCH_ERROR = 3  # API unreachable, or an answer we cannot use
    STALE = 4  # last successful call is too old to be trusted


class TempoProvider:
    """
    Provider class to fetch Tempo day information from EDF API.
    Tempo is a French electricity pricing system with three colors:
    - Blue (Bleu): Low price
    - White (Blanc): Normal price
    - Red (Rouge): High price
    """

    BASE_URL = "https://www.api-couleur-tempo.fr/api/jourTempo"

    # Fallback used when the caller does not tell us how often it refreshes.
    DEFAULT_STALE_AFTER_S = 6 * 3600

    def __init__(self, stale_after_s: int = DEFAULT_STALE_AFTER_S):
        self._stale_after = timedelta(seconds=stale_after_s)
        self._today_price: DayPrice = DayPrice.UNKNOWN
        self._tomorrow_price: DayPrice = DayPrice.UNKNOWN
        self._today_status: DayStatus = DayStatus.NEVER_FETCHED
        self._tomorrow_status: DayStatus = DayStatus.NEVER_FETCHED
        self._today_data: Optional[dict] = None
        self._tomorrow_data: Optional[dict] = None
        self._last_success: Optional[datetime] = None

    def _map_code_to_price(self, code_day: int) -> DayPrice:
        if code_day == 1:
            return DayPrice.LOW
        elif code_day == 2:
            return DayPrice.NORMAL
        elif code_day == 3:
            return DayPrice.HIGH
        elif code_day == 0:
            # Expected every morning : EDF publishes tomorrow's colour around 11:00.
            LOGGER.info("Tempo codeJour 0 : colour not published yet")
            return DayPrice.UNKNOWN
        else:
            LOGGER.warning(f"Unknown Tempo codeJour: {code_day}")
            return DayPrice.UNKNOWN

    @staticmethod
    def _map_code_to_status(code_day: int, price: DayPrice) -> DayStatus:
        if price != DayPrice.UNKNOWN:
            return DayStatus.OK
        # codeJour 0 is the API saying "not published yet", anything else is junk.
        return DayStatus.NOT_PUBLISHED if code_day == 0 else DayStatus.FETCH_ERROR

    def _fetch_tempo_day(self, endpoint: str) -> Optional[dict]:
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            LOGGER.info(f"Fetching Tempo data from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                LOGGER.error(f"Unexpected Tempo {endpoint} payload type: {type(data).__name__}")
                return None
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
        api_reached = False

        today_data = self._fetch_tempo_day("today")
        if today_data is not None:
            code_day = today_data.get("codeJour", 0)
            self._today_data = today_data
            self._today_price = self._map_code_to_price(code_day)
            self._today_status = self._map_code_to_status(code_day, self._today_price)
            api_reached = True
            LOGGER.info(f"Today's Tempo price: {self._today_price.name} ({self._today_status.name})")
        else:
            self._today_price = DayPrice.UNKNOWN
            self._today_status = DayStatus.FETCH_ERROR
            LOGGER.warning("Failed to update today's Tempo price")

        tomorrow_data = self._fetch_tempo_day("tomorrow")
        if tomorrow_data is not None:
            code_day = tomorrow_data.get("codeJour", 0)
            self._tomorrow_data = tomorrow_data
            self._tomorrow_price = self._map_code_to_price(code_day)
            self._tomorrow_status = self._map_code_to_status(code_day, self._tomorrow_price)
            api_reached = True
            LOGGER.info(f"Tomorrow's Tempo price: {self._tomorrow_price.name} ({self._tomorrow_status.name})")
        else:
            self._tomorrow_price = DayPrice.UNKNOWN
            self._tomorrow_status = DayStatus.FETCH_ERROR
            LOGGER.warning("Failed to update tomorrow's Tempo price")

        if api_reached:
            self._last_success = datetime.now()

    def is_stale(self) -> bool:
        """True when the last successful call is too old to be trusted."""
        if self._last_success is None:
            return True
        return (datetime.now() - self._last_success) > self._stale_after

    def _trusted(self, price: DayPrice, status: DayStatus):
        """Drop a cached colour we can no longer vouch for."""
        if status == DayStatus.OK and self.is_stale():
            return DayPrice.UNKNOWN, DayStatus.STALE
        return price, status

    def get_today_price(self) -> DayPrice:
        """Today's electricity price level, as published by the API."""
        return self._trusted(self._today_price, self._today_status)[0]

    def get_tomorrow_price(self) -> DayPrice:
        """Tomorrow's electricity price level, as published by the API."""
        return self._trusted(self._tomorrow_price, self._tomorrow_status)[0]

    def get_today_status(self) -> DayStatus:
        """Why get_today_price() holds the value it holds."""
        return self._trusted(self._today_price, self._today_status)[1]

    def get_tomorrow_status(self) -> DayStatus:
        """Why get_tomorrow_price() holds the value it holds."""
        return self._trusted(self._tomorrow_price, self._tomorrow_status)[1]

    def get_last_success(self) -> Optional[datetime]:
        """When the API was last reached, or None if it never was."""
        return self._last_success

    def get_price_for_upcoming_tempo_day(self, now: Optional[datetime] = None) -> DayPrice:
        """Colour of the next Tempo day to start : the one worth pre-heating for.

        A Tempo day starts at 06:00, so before 06:00 the day about to start is
        the API's "today", and from 06:00 onwards it is the API's "tomorrow".
        Always reading "tomorrow" meant pre-heating never triggered during an
        off-peak window placed between midnight and 06:00.
        """
        now = now or datetime.now()
        if now.hour < TEMPO_DAY_START_HOUR:
            return self.get_today_price()
        return self.get_tomorrow_price()

    def get_price_for_current_tempo_day(self, now: Optional[datetime] = None) -> DayPrice:
        """Colour currently being billed.

        Before 06:00 the Tempo day in effect started yesterday at 06:00, and we
        do not fetch yesterday : report UNKNOWN instead of guessing. That is also
        the correct behaviour, since a red tariff only starts at 06:00 and no
        reduction should be applied before then.
        """
        now = now or datetime.now()
        if now.hour < TEMPO_DAY_START_HOUR:
            return DayPrice.UNKNOWN
        return self.get_today_price()

    def get_today_data(self) -> Optional[dict]:
        """Get raw today's Tempo data."""
        return self._today_data

    def get_tomorrow_data(self) -> Optional[dict]:
        """Get raw tomorrow's Tempo data."""
        return self._tomorrow_data

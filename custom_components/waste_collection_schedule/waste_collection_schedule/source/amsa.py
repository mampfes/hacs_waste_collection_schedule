import time
import datetime
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentRequired,
    SourceArgumentExceptionMultiple,
    SourceArgumentException,
)

TITLE = "AMSA"
DESCRIPTION = "Source for AMSA (Milan, Italy) waste collection."
URL = "https://www.amsa.it/it/milano"
COUNTRY = "it"

TEST_CASES = {
    "monte_rosa_91": {
        "address": "Via Monte Rosa",
        "house_number": "91",
        "city": "Milano",
    },
    "piazza_duomo_1": {
        "address": "Piazza del Duomo",
        "house_number": "1",
        "city": "Milano",
    },
    "viale_piave_40b": {
        "address": "Viale Piave",
        "house_number": "40B",
        "city": "Milano",
    },
}

API_URL = URL + "/servizi/raccolta-differenziata?popup=services&serviceType=sdz"
ICON_MAP = {
    "indifferenziato": "mdi:trash-can",
    "organico": "mdi:leaf",
    "carta e cartone": "mdi:package-variant",
    "plastica e metallo": "mdi:recycle",
    "vetro": "mdi:bottle-soda",
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You need to provide the street name and house number "
    "of your address, as well as the city.",
    "it": "Devi fornire il nome della via e il numero civico "
    "del tuo indirizzo, oltre alla città.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The street name of your address in Milan "
        "(e.g., 'Via Monte Rosa').",
        "house_number": "The house number of your address in Milan "
        "(e.g., '91').",
        "city": "The city of your address (e.g., 'Milano').",
    },
    "it": {
        "address": "Il nome della via del tuo indirizzo a Milano "
        "(ad esempio, 'Via Monte Rosa').",
        "house_number": "Il numero civico del tuo indirizzo a Milano "
        "(ad esempio, '91').",
        "city": "La città del tuo indirizzo (ad esempio, 'Milano').",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
        "house_number": "House Number",
        "city": "City",
    },
    "it": {
        "address": "Indirizzo",
        "house_number": "Numero Civico",
        "city": "Città",
    }
}


class Source:
    def __init__(
        self, address: str, house_number: str, city: Optional[str] = None
    ):
        """Create a new source for AMSA.

        Validation rules:
        - `address` is required and must be a non-empty string.
        - `house_number` is required and must be a non-empty string or int.
        - `city` is optional. If provided it must be a non-empty string.

        The Selenium WebDriver is not started here until fetch/collection is run.
        """

        errors: List[tuple] = []

        # Validate address
        if address is None or (
            isinstance(address, str) and address.strip() == ""
        ):
            errors.append(("address", "address must be a non-empty string"))

        # Validate house_number
        if house_number is None or (
            isinstance(house_number, str) and house_number.strip() == ""
        ):
            errors.append(
                (
                    "house_number",
                    "house_number must be provided and non-empty",
                )
            )

        # Validate city (optional)
        if city is not None and (
            not isinstance(city, str) or city.strip() == ""
        ):
            errors.append(("city", "city must be a non-empty string when provided"))

        # If multiple errors, raise the multiple-argument exception
        if len(errors) > 1:
            arg_names = [arg for arg, _ in errors]
            message = ", ".join([f"{a}: {m}" for a, m in errors])
            raise SourceArgumentExceptionMultiple(arg_names, message)

        # If single error, raise the single-argument exception or required exception
        if len(errors) == 1:
            arg, msg = errors[0]
            if arg in ("address", "house_number"):
                raise SourceArgumentRequired(arg, msg)
            raise SourceArgumentException(arg, msg)

        # Store sanitized values
        self._address = str(address).strip()
        self._house_number = str(house_number).strip()
        self._city = str(city).strip() if city is not None else None
        self._driver: Optional[WebDriver] = None

    def proceed_to_next_month(self) -> bool:
        try:
            next_button = self._driver.find_element(
                By.CSS_SELECTOR, "button.fc-next-button.fc-button.fc-button-primary"
            )
            if next_button.get_attribute("disabled"):
                return False  # No next month available
            next_button.click()
            time.sleep(1)
            return True
        except Exception as e:
            raise Exception("Could not navigate to the next month: " + str(e)) from e

    def collect_waste_for_month(self) -> Dict[str, List[str]]:
        days = self._driver.find_elements(By.CSS_SELECTOR, "td[data-date]")
        month_data: Dict[str, List[str]] = {}
        if not days or len(days) == 0:
            raise Exception("No days found in the calendar.")
        try:
            for day in days:
                date = day.get_attribute("data-date")
                events = [
                    img.get_attribute("alt").replace("Raccolta ", "").strip()
                    for img in day.find_elements(
                        By.CSS_SELECTOR, ".area-services-calendar_eventIcon__qFA7O"
                    )
                ]
                if events:
                    polished_events = [
                        event.lower() for event in events if event in ICON_MAP.keys()
                    ]
                    month_data[date] = polished_events
        except Exception as e:
            raise Exception("Could not extract waste collection data: " + str(e)) from e
        return month_data

    def collect_waste_collection_schedule(self):
        # Initialize WebDriver lazily (only when collecting data)
        if self._driver is None:
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")
                self._driver = webdriver.Chrome(options=options)
                self._driver.get(API_URL)
                self._driver.implicitly_wait(20)  # Wait for elements to load
            except Exception as e:
                raise Exception(
                    "Could not start the web driver. Ensure that ChromeDriver is installed"
                ) from e

        # Accept cookies if the popup appears
        try:
            accept_cookies_button = self._driver.find_element(
                By.CLASS_NAME, "iubenda-cs-close-btn"
            )
            accept_cookies_button.click()
        except Exception:
            pass  # If the button is not found, continue

        try:
            address_field = self._driver.find_element(
                By.CSS_SELECTOR, "[class^='input-text'] input"
            )
            address_field.click()
            time.sleep(1)  # Small delay to ensure the field is ready
            address_str = f"{self._address} {self._house_number}"
            if self._city:
                address_str = f"{address_str}, {self._city}"
            address_field.send_keys(address_str)
        except Exception as e:
            self._driver.quit()
            raise Exception("Could not find the address input field: " + str(e)) from e

        try:
            # Wait for the dropdown with suggestions and select the first one
            self._driver.implicitly_wait(5)  # Wait for suggestions to load
            suggestions = self._driver.find_elements(
                By.CLASS_NAME, "area-services_formInputField__svC8K"
            )
            suggestions[0].click()
        except Exception as e:
            self._driver.quit()
            raise Exception("Could not select the address from suggestions: " + str(e)) from e

        try:
            # Wait until calendar loads
            time.sleep(2)  # Small delay to ensure the calendar button is clickable
            calendar_button = self._driver.find_element(
                By.CSS_SELECTOR, "[class^='area-services_btnOpenCalendar__C8q8E']"
            )
            calendar_button.click()
        except Exception as e:
            self._driver.quit()
            raise Exception("Could not open the calendar: " + str(e)) from e

        try:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
        except Exception as e:
            self._driver.quit()
            raise Exception("Calendar did not load in time: " + str(e)) from e

        try:
            collections = self.collect_waste_for_month()
            while self.proceed_to_next_month():
                month_collections = self.collect_waste_for_month()
                collections.update(month_collections)
        except Exception as e:
            self._driver.quit()
            raise Exception("Could not extract collections: " + str(e)) from e

        self._driver.quit()
        return collections

    def fetch(self) -> List[Collection]:
        # Use Selenium to scrape the data
        calendar_data = self.collect_waste_collection_schedule()

        entries: List[Collection] = []
        for date_str, events in calendar_data.items():
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            for event in events:
                event_lower = event.lower()
                icon = ICON_MAP.get(event_lower, "mdi:trash-can")
                entries.append(Collection(date=date, t=event, icon=icon))

        entries.sort(key=lambda x: x.date)
        return entries

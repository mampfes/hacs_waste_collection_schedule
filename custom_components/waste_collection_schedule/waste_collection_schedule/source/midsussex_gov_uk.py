import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

# --- METADATA AND ICONS ---
TITLE = "Mid Sussex District Council (Whitespace WRP)"
DESCRIPTION = "Source script for Mid Sussex District Council. Fetches collection dates using a four-step web scraping process on the Whitespace Waste & Recycling Portal."
URL = "https://www.midsussex.gov.uk/waste-and-recycling/"

# Date format for the final page: DD/MM/YYYY
DATE_FORMAT = "%d/%m/%Y"

# *** TEST CASES ***
TEST_CASES = {
    # 1. Simple Numerical Address
    "Test Case 1: 23 High Street": {"number": "23", "street": "HIGH STREET", "postcode": "RH17 6TB"},
    
    # 2. Complex Named Property
    "Test Case 2: Hapstead Hall": {"number": "HAPSTEAD HALL", "street": "HIGH STREET", "postcode": "RH17 6TB"},
    
    # 3. Commercial/Pub Named Property
    "Test Case 3: The Gardeners Arms": {"number": "THE GARDENERS ARMS", "street": "SELSFIELD ROAD", "postcode": "RH17 6TJ"},
}

ICON_MAP = {
    "DOMESTIC FOOD WASTE SERVICE": "mdi:food-apple",
    "DOMESTIC RECYCLING WASTE COLLECTION SERVICE": "mdi:recycle",
    "DOMESTIC REFUSE WASTE COLLECTION SERVICE": "mdi:trash-can",
    "DOMESTIC GARDEN WASTE SERVICE": "mdi:leaf",
    # Add other types as needed
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your property's exact Postcode, Street Name, and House Name/Number (or business name) as they appear on the council's website's collection search tool.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "number": "Enter the house name (e.g., HAPSTEAD HALL) or number (e.g., 11), or the business name.",
        "street": "Enter the street name (e.g., HIGH STREET).",
        "postcode": "Enter the postcode (e.g., RH17 6TB).",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "number": "House/Business Name/Number",
        "street": "Street Name",
        "postcode": "Postcode",
    },
}

#### End of arguments affecting the configuration GUI ####

# --- SOURCE CLASS ---

class Source:
    def __init__(self, number: str, street: str, postcode: str):
        # We clean and store the inputs
        self._number = number.strip()
        self._street = street.strip()
        self._postcode = postcode.strip().replace(" ", "+") # URL-encode space

    def fetch(self) -> list[Collection]:
        entries = []
        BASE_URL = "https://sms-wrp.whitespacews.com"

        with requests.Session() as session:
            # --- STEP 1: Get the Dynamic Track Token ---
            r1 = session.get(f"{BASE_URL}/mop.php")
            r1.raise_for_status()

            soup = BeautifulSoup(r1.text, 'html.parser')

            next_link_element = soup.find('a', href=lambda href: href and 'Track=' in href)

            if not next_link_element:
                 raise Exception("Could not find dynamic Track token link in Step 1.")

            dynamic_link = next_link_element.get('href')

            try:
                track_token = dynamic_link.split('Track=')[1].split('&')[0]
            except IndexError:
                raise Exception("Could not parse dynamic Track token in Step 1.")

            # --- STEP 2: Submit the Address ---
            post_url = f"{BASE_URL}/mop.php?serviceID=A&Track={track_token}&seq=2"

            payload = {
                'address_name_number': self._number,
                'address_street': self._street,
                'street_town': '',
                'address_postcode': self._postcode.replace('+', ' '), # Send post data un-encoded
            }

            r2 = session.post(post_url, data=payload)
            r2.raise_for_status()

            # --- STEP 3: Select the Specific Address (Get pIndex) ---
            soup2 = BeautifulSoup(r2.text, 'html.parser')

            search_text = self._number.upper()

            address_link = soup2.find(
                'a',
                class_='app-subnav__link',
                string=lambda t: t and search_text in t.upper()
            )

            if not address_link:
                if soup2.find(string=lambda t: t and "address not listed" in t.lower()):
                    raise SourceArgumentException(
                        "Address not found. Check house name/number and postcode.",
                        argument="number"
                    )
                raise Exception(f"Could not find the address link for '{self._number}'.")

            final_link_path = address_link['href']
            final_schedule_url = f"{BASE_URL}/{final_link_path}"

            # --- STEP 4: Scrape the Final Schedule ---
            r3 = session.get(final_schedule_url)
            r3.raise_for_status()

            soup3 = BeautifulSoup(r3.text, 'html.parser')

            collection_entries = soup3.find_all('ul', class_='displayinlineblock')

            if not collection_entries:
                if soup3.find(string=lambda t: t and "not available" in t.lower()):
                    return [] # Return empty list if schedule is unavailable
                raise Exception("Could not find any collection entries on the schedule page.")

            for ul in collection_entries:
                list_items = ul.find_all('li')

                if len(list_items) < 3:
                    continue

                date_str = list_items[1].p.text.strip()
                waste_type = list_items[2].p.text.strip().upper()

                try:
                    collection_date = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
                except ValueError:
                    print(f"Skipping entry with unparsable date format: {date_str}")
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

            return entries
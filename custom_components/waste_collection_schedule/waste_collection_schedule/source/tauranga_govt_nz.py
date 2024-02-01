import json
import requests
from urllib.parse import quote, urlencode
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection


TITLE = "Tauranga City Council"
DESCRIPTION = "Source script for Tauranga City Council"
URL = "https://www.tauranga.govt.nz/"
TEST_CASES = {
    "121 Castlewold Drive": {"address": "121 Castlewold Drive"},
    "70 Santa Monica Drive": {"address": " 70 Santa Monica Drive"},
    "21 Wells Avenue": {"address": " 21 Wells Avenue"},
}

API_URL = "https://www.tauranga.govt.nz/living/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out"
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "Garden waste": "mdi:leaf",
    "Food scraps": "mdi:food-apple",
}


class Source:
    def __init__(self, address):
        self._address = address
        self._session = requests.session()

    ADDRESS_URL = "https://www.tauranga.govt.nz/Services/SearchService.asmx/DoRIDStreetPredictiveSearch"
    WASTE_URL = "https://www.tauranga.govt.nz/living/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out"

    def fetch(self):
        addr1, addr2 = self._get_address_detail()
        form_data = self._generate_form_data(addr1, addr2)
        waste_response = self._get_waste_pickup_dates(form_data)

        return self._parse_waste_pickup_dates(waste_response)

    def _get_address_detail(self):
        address_response = self._session.post(
            self.ADDRESS_URL,
            json={"prefixText": self._address, "count": 12, "contextKey": "test"},
            headers={"Content-Type": "application/json; charset=UTF-8"},
        ).json()

        if len(address_response.get("d")) == 0:
            raise Exception("Address not found within TCC records")

        address_object = json.loads(address_response["d"][0])
        addr_1 = address_object.get("First")
        addr_2 = address_object.get("Second")

        return addr_1, addr_2

    def _generate_form_data(self, addr_1, addr_2):
        # Stripped down form data needed to post a successful request.
        form_data = {
            "dnn$ctr2863$MasterView$CollectionDaysv2$Address": addr_1,
            "dnn$ctr2863$MasterView$CollectionDaysv2$hdnValue": addr_1 + "||" + addr_2,
            "__VIEWSTATE": "6nUGBMQiwd8snplmXFH9MJGF1QDiPwz54NSFyduo8Md08wuEan6H3mlQRo7UFIAvumpfnuuXjypccG+2xaLJJ5i6L4enYURj0te5zQcvPUN3fl2/1kjHAGROCPVBhZs1TVHN4Do/dQejPQq2Tgi/Dma9PBkexJ8pW+T2LxEfTKaKB8nRl1NDmm9Ql+nqnG2syRVs/J1oO2iVNGfPj/4xv/HyNA/XtXCFNMq8kpKdt3ur8S9yPTy51tn+oGeXOHw6wSeVJBcFipZyjHPoAag0QGd0NZ3Q8tjR4L5BSnn1PkRLPYehKub/I7HI1iCDbccYVdUkSYkzG9g9G9to9kCDx3/rDlYkSjcL/Eq/thACDiN1LNbnrKDJtVPWKVX+69I7wJ+xNM2iK7RXslUVpBU0ta6crbR1uPGUGOIJFvtXrmZupKITmetn9eoM1GkJLHjO2333RVhiHlYzCa2Xieq63By3pXnsWwk19Jq979WpC47tNuDzjYuL40HZwzOWo/QqoE8ABUHC71g7zUAIyWg4ldSHXjmyrnQEyu90fqSrdeNb6LXX4vK3I2WtO1oOsg9TjL0C6Oq6moYJ7ycZh44eI2mCswpS0CI3D3UXpJ1LFpTew+qyEYtXunosm/zp63UvhSf/7tz3AGKcUYqQaoCgEGzMPamCtY/Ngw8AoUdXb9LwiNv4OZhZn0J6nRqLXV3qC/Ig1jchsoK/nPCVy4Aymj4i0BrCLs+KdFr6vChSHunE9xoFXl+nPXfxTKB6Gc3vnE/2C+2fzS2GgIyWbJOUj4Co24TVovKLs6rZWMPibSUHW+RNbsb3e9f91zr7b6AA8GwS90OsHCFNbeF3/yWlGMNJnBfx2l7P+2DmcuuD/oi5CxTmeBHBQQHPw8YLqzUxKWGSWxISejDssa8lydfhso3ag59FgDuoq1Fcit8JRnezuC9gKDRn9q3Efhzk/zZuaS8ryrAw2wxZM84dk5T5CGAEM8QbtK5e+kH05UkmLKHXzPPXoyadwu/jH8c4/doayvq5XfD37n/evwR7K/fUiyG3hHDfD4XtQvyA6PhovN+zOjNeqD9sp378OXhYXLLrk1g1aHM7jOtM6sTniVhLsmcxmCj8whjAMLG6++DtvQkdDjmDULmJHQJ9lfZYbksnoW3HFd/6OaqCHLndxspBJyq9XdCWco3eipfhUoPd2c+ZfC5WiM2WwtpPr6iDBqoGDKfhLaJIiWX5cyexZlDkjlYx/g2oZg/Xc2lx4KaEjuHoJiJ+BG/As5EXNIbwSs61+Mh7VkPuab9fMe1+HVcNwe/WJySizXdSkstZYcNQzM8zUCMetTPY/j5litylfTu4nAhWdPvbqscMYSnyrGe3XOdaGWNNvLJDHtuXCKDg50KUV3HIiHQcLEwsKwrtXm9ul1rrUibB1yKsltkXgIge4kaT6Su2spNqTC4SEOdCShalgVGf0x2p7bFKqFJmPgoFY+dOJsYMX80NIX8bQ/vkHuDprumd1jswv9PiGiyS+NrbSntV/8ERRArDB1ql9GLAWQz7B/nmkGNHAfYm",
            "__EVENTVALIDATION": "Y3fGKXkZMTst2XAMZ5VMemVAEezov7cltij3trOIsKLqmnrspUGeIn1vvNW92YJRAOBUNIEaQ/Ro46A9wYH69QUK8yE4lqgnrYBKdtrqq87emk9ujpYjrZ4/+y4P/4/zWDJbwRxXcrhgjb89zD8bSQVQnVrQLUycWmToH8a/okcSPVR3mVDgxsmGcG0SipxOEinlhtNTJUSAs/pCSoI7unIg0siP3no4rAxrDLHcN5d5Jnf4",
        }

        encoded_form_data = urlencode(form_data, quote_via=quote)

        return encoded_form_data

    def _get_waste_pickup_dates(self, form_data):
        pickup_date_response = self._session.post(
            self.WASTE_URL,
            data=form_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
        )

        return pickup_date_response

    def _parse_waste_pickup_dates(self, pickup_date_response):
        soup = BeautifulSoup(pickup_date_response.text, "html.parser")
        bin_type_containers = soup.find_all("div", class_="binTypeContainer")

        entries = []

        for container in bin_type_containers:
            date = container.find("h5").text.strip()
            bin_types = [
                item.text
                for item in container.find_all("p")
                if item.find("span", class_="dot")
            ]
            if date == "Not subscribed":
                break  # Skip waste types that aren't being paid for/subscribed to.
            else:
                current_date = datetime.now()
                pickup_date = datetime.strptime(date, "%A %d %B")

                if current_date.month == "12" and pickup_date.month == "1":
                    # If it's current December and the pickup date is January, then the year needs to be incremented
                    pickup_date = pickup_date.replace(
                        year=datetime.now().year + 1
                    ).date()

                pickup_date = pickup_date.replace(year=datetime.now().year).date()

            for t in bin_types:
                entries.append(
                    Collection(
                        date=pickup_date,
                        t=t,
                        icon=ICON_MAP.get(t, "mdi:help"),
                    )
                )

        return entries

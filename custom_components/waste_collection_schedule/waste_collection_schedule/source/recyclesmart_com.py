import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "RecycleSmart"
DESCRIPTION = "Source for RecycleSmart collection."
URL = "https://www.recyclesmart.com/"
COUNTRY = "au"
TEST_CASES = {
    "pickup": {
        "email": "!secret recyclesmart_email",
        "password": "!secret recyclesmart_password"
    },
}


class Source:
    def __init__(self, email, password):
        self._email = email
        self._password = password

    def fetch(self):
        # login is via Google Identity Toolkit, providing username and password.
        r = requests.post(
            "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
            json={
                "returnSecureToken": True,
                "email": self._email,
                "password": self._password,
            },
            params={"key": "AIzaSyBnup3QFYYGwnvjZi7r5a39c8b94SNospU"},
        )
        data = json.loads(r.text)

        # take the token returned from Google Identity Toolkit to get the API auth token (JWT) from Firebase
        r = requests.post(
            "https://www.app.recyclesmart.com/api/sessions/firebase",
            json={"id_token": data["idToken"]},
            headers={"content-type": "application/json"},
        )
        data = json.loads(r.text)

        # use the auth token (jwt) from firebase to get pickups
        r = requests.get(
            "https://www.app.recyclesmart.com/api/pickups",
            # retrieves future pickups (if scheduled), then past pickups, until per_page is reached
            # the average user is scheduled for monthly pickups
            params={"page":"1", "per_page":"5"},
            headers={"Authorization": data["data"]["attributes"]["auth_token"]},
        )

        data = json.loads(r.text)

        entries = []
        for item in data["data"]:
            collection_date = datetime.strptime(item["attributes"]["pickup_on"], "%Y-%m-%d")
            entries.append(Collection(collection_date.date(), "Pickup"))
        return entries

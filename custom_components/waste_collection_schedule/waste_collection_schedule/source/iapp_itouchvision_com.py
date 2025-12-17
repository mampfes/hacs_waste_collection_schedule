import binascii
import json
from datetime import datetime
from typing import Literal, TypedDict

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from waste_collection_schedule import Collection


class Municipality(TypedDict):
    PAYLOAD: dict[str, str | int]
    API_URL: str
    title: str
    url: str


TITLE = "iTouchVision Source using the encrypted API"
DESCRIPTION = "Source for iTouchVision Source using the encrypted API."
URL = "https://www.itouchvision.com/"
TEST_CASES = {
    "chiltern: 100080550517": {"uprn": 100080550517, "municipality": "BUCKINGHAMSHIRE"},
    "newport: 10090955364": {"uprn": "10090955364", "municipality": "NEWPORT"},
    "blaenau gwent: 100100457787": {
        "uprn": "100100457787",
        "municipality": "BLAENAU GWENT",
    },
    "Winchester: 10090844134": {"uprn": "10090844134", "municipality": "WINCHESTER"},
    "Aylesbury Vale: 766251559": {
        "uprn": 766251559,
        "municipality": "AYLESBURY VALE",
    },
    "Somerset (including former merged councils)": {
        "uprn": 30071272,
        "municipality": "SOMERSET",
    },
    "Test Valley": {"uprn": 100060571645, "municipality": "TEST VALLEY"},
    "Hyndburn": {"uprn": 100010439798, "municipality": "HYNDBURN"},
}
COUNTRY = "uk"
ICON_MAP = {
    "Food waste": "mdi:food",
    "Food Waste": "mdi:food",
    "FOOD WASTE": "mdi:food",
    "General waste": "mdi:trash-can",
    "Mixed recycling": "mdi:recycle",
    "Paper and cardboard": "mdi:newspaper",
    "Textiles/Batteries/Electricals": "mdi:battery",
    "GARDEN WASTE": "mdi:flower",
    "Garden waste": "mdi:flower",
    "HOUSEHOLD WASTE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "Recycling collection": "mdi:recycle",
    "Refuse Bin": "mdi:trash-can",
    "Garden Waste Collection": "mdi:flower",
    "General Waste Collection": "mdi:trash-can",
    "Glass Collection": "mdi:bottle-wine",
    "Recycling Collection": "mdi:recycle",
    "Garden": "mdi:flower",
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
    "Garden Waste": "mdi:flower",
    "Household Waste": "mdi:trash-can",
    "RECYCLING - BLUE": "mdi:recycle",
    "RECYCLING - BROWN": "mdi:newspaper",
    "RECYCLING - GREEN": "mdi:leaf",
    "REFUSE": "mdi:trash-can",
    "Green Garden Waste": "mdi:leaf",
}

# Global variables for encryption key and IV
KEY = binascii.unhexlify(
    "F57E76482EE3DC3336495DEDEEF3962671B054FE353E815145E29C5689F72FEC"
)
IV = binascii.unhexlify("2CBF4FC35C69B82362D393A4F0B9971A")


# Encryption function
def encrypt_aes(plaintext: str) -> str:
    data = plaintext.encode("utf-8")
    padded_data = pad(data, AES.block_size)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ciphertext = cipher.encrypt(padded_data)
    return binascii.hexlify(ciphertext).decode("utf-8")


# Decryption function
def decrypt_aes(ciphertext_hex: str) -> str:
    ciphertext = binascii.unhexlify(ciphertext_hex)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted_data = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted_data, AES.block_size).decode("utf-8")
    return plaintext


MUNICIPALITIES: dict[str, Municipality] = {
    "BUCKINGHAMSHIRE": {
        "PAYLOAD": {
            "P_CLIENT_ID": 152,
            "P_COUNCIL_ID": 34505,
        },
        "API_URL": "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
        "title": "Buckinghamshire: Formerly (Chiltern, South Bucks, Wycombe)",
        "url": "https://www.buckinghamshire.gov.uk/",
    },
    "NEWPORT": {
        "PAYLOAD": {
            "P_CLIENT_ID": 130,
            "P_COUNCIL_ID": 260,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Newport City Council",
        "url": "https://www.newport.gov.uk/",
    },
    "BLAENAU GWENT": {
        "PAYLOAD": {
            "P_CLIENT_ID": 106,
            "P_COUNCIL_ID": 35,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Blaenau Gwent County Borough Council",
        "url": "https://www.blaenau-gwent.gov.uk/",
    },
    "WINCHESTER": {
        "PAYLOAD": {
            "P_CLIENT_ID": 43,
            "P_COUNCIL_ID": 433,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Winchester City Council",
        "url": "https://www.winchester.gov.uk",
    },
    "AYLESBURY VALE": {
        "PAYLOAD": {
            "P_CLIENT_ID": 152,
            "P_COUNCIL_ID": 34505,
        },
        "API_URL": "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
        "title": "Aylesbury Vale District Council",
        "url": "https://www.aylesburyvaledc.gov.uk/",
    },
    "SOMERSET": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Somerset Council",
        "url": "https://www.somerset.gov.uk/",
    },
    "SOUTH SOMERSET": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "South Somerset District Council",
        "url": "https://www.southsomerset.gov.uk/",
    },
    "MENDIP": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Mendip District Council",
        "url": "https://www.mendip.gov.uk/",
    },
    "SEDGEMOOR": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Sedgemoor District Council",
        "url": "https://www.sedgemoor.gov.uk",
    },
    "SOMERSET WEST AND TAUNTON": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Somerset West & Taunton District Council",
        "url": "https://www.somersetwestandtaunton.gov.uk/",
    },
    "SOMERSET COUNTY": {
        "PAYLOAD": {
            "P_CLIENT_ID": 129,
            "P_COUNCIL_ID": 34493,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Somerset County Council",
        "url": "https://www.somerset.gov.uk/",
    },
    "TEST VALLEY": {
        "PAYLOAD": {
            "P_CLIENT_ID": 94,
            "P_COUNCIL_ID": 390,
        },
        "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "title": "Test Valley Borough Council",
        "url": "https://www.testvalley.gov.uk/",
    },
    "HYNDBURN": {
        "PAYLOAD": {
            "P_CLIENT_ID": 157,
            "P_COUNCIL_ID": 34508,
        },
        # "API_URL": "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay",
        "API_URL": "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
        "title": "Hyndburn Borough Council",
        "url": "https://www.hyndburnbc.gov.uk/",
    },
}

MUNICIPALITY_LITERALS = Literal[
    "BUCKINGHAMSHIRE",
    "NEWPORT",
    "BLAENAU GWENT",
    "WINCHESTER",
    "AYLESBURY VALE",
    "SOMERSET",
    "SOUTH SOMERSET",
    "MENDIP",
    "SEDGEMOOR",
    "SOMERSET WEST AND TAUNTON",
    "SOMERSET COUNTY",
    "TEST VALLEY",
    "HYNDBURN",
]

EXTRA_INFO = [
    {
        "title": m["title"],
        "url": m["url"],
        "country": COUNTRY,
        "default_params": {"municipality": key},
    }
    for key, m in MUNICIPALITIES.items()
]


class Source:
    def __init__(self, uprn: str | int, municipality: MUNICIPALITY_LITERALS):
        self._uprn: str | int = uprn
        if not municipality.upper() in MUNICIPALITIES:
            raise ValueError(f"Unknown municipality: {municipality}")
        self._payload = MUNICIPALITIES[municipality.upper()]["PAYLOAD"]
        self._api_url = MUNICIPALITIES[municipality.upper()]["API_URL"]

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Prepare the data to be encrypted
        payload: dict[str, str | int] = {
            "P_UPRN": self._uprn,
            **self._payload,
            "P_LANG_CODE": "EN",
        }

        # Encrypt the payload
        encrypted_payload = encrypt_aes(json.dumps(payload))

        # Send the request with the encrypted data
        response = session.post(
            self._api_url,
            data=encrypted_payload,
            headers={
                # "user-agent":"Mozilla/5.0",
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "*/*",
            },
        )
        response.raise_for_status()

        # Decrypt the response
        decrypted_response = decrypt_aes(response.text)

        # Parse the JSON response
        servicedata = json.loads(decrypted_response)

        # Process the collection dates
        entries = []
        for service in servicedata["collectionDay"]:
            collection_dates = [
                datetime.strptime(service["collectionDay"], "%d-%m-%Y").date()
            ]
            try:
                collection_dates.append(
                    datetime.strptime(service["followingDay"], "%d-%m-%Y").date()
                )
            except Exception:
                pass
            bin_type = service["binType"].split(" (")[0].split(":")[0]
            for collection_date in collection_dates:
                entries.append(
                    Collection(
                        date=collection_date, t=bin_type, icon=ICON_MAP.get(bin_type)
                    )
                )

        return entries

import re
import base64
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii

TITLE = "Buckinghamshire Waste Collection - Former Chiltern, South Bucks or Wycombe areas"
DESCRIPTION = "Source for chiltern.gov.uk services for parts of Buckinghamshire"
URL = "https://chiltern.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "200000811701"},
    "Test_002": {"uprn": "100080550517"},
    "Test_003": {"uprn": "100081091932"},
    "Test_004": {"uprn": 10094593823},
}

ICON_MAP = {
    "Food waste": "mdi:food",
    "General waste": "mdi:trash-can",
    "Mixed recycling": "mdi:recycle",
    "Paper and cardboard": "mdi:newspaper",
    "Textiles/Batteries/Electricals": "mdi:battery",
}

# Global variables for encryption key and IV
KEY = binascii.unhexlify("F57E76482EE3DC3336495DEDEEF3962671B054FE353E815145E29C5689F72FEC")
IV = binascii.unhexlify("2CBF4FC35C69B82362D393A4F0B9971A")

# Encryption function
def encrypt_aes(plaintext):
    data = plaintext.encode('utf-8')
    padded_data = pad(data, AES.block_size)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ciphertext = cipher.encrypt(padded_data)
    return binascii.hexlify(ciphertext).decode('utf-8')

# Decryption function
def decrypt_aes(ciphertext_hex):
    ciphertext = binascii.unhexlify(ciphertext_hex)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted_data = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted_data, AES.block_size).decode('utf-8')
    return plaintext

class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()

        # Prepare the data to be encrypted
        payload = {
            "P_UPRN": self._uprn,
            "P_CLIENT_ID": 152,
            "P_COUNCIL_ID": 34505,
            "P_LANG_CODE": "EN"
        }
        
        # Encrypt the payload
        encrypted_payload = encrypt_aes(json.dumps(payload))

        # Send the request with the encrypted data
        response = session.post(
            "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay",
            data=encrypted_payload,
            headers={
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
        for service in servicedata['collectionDay']:
            collection_date = datetime.strptime(service['collectionDay'], '%d-%m-%Y').date()
            bin_type = service['binType']
            entries.append(
                Collection(
                    date=collection_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type)
                )
            )

        return entries

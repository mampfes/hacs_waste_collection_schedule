import requests
import json

import datetime
# from waste_collection_schedule import Collection
# from waste_collection_schedule.service.ICS import ICS

DESCRIPTION = "Example source for abc.com"
URL = "https://www.awista-kommunal.de"
TEST_CASES = {
    "complete_street": {
        "street": '["Zeppenheimer Straße 141"]'.encode("utf8"),
    },
    "complete_street_no_nr": {
        "street": '["Zeppenheimer Straße"]'.encode("utf8"),
    },
    "incomplete_street": {
        "street": '["Zeppenhei"]'.encode("utf8"),
    },
    "no_street": {
        "street": '["z"]'.encode("utf8"),
    },
}

# https://www.awista-kommunal.de/abfallkalender/0aefebe8-3ad9-481e-ab38-ac64bb4fb912

url = "https://awista-kommunal.de/abfallkalender"

# confirmed working header for Post request
headers = {
    "Host": "www.awista-kommunal.de",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Accept": "text/x-component",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.awista-kommunal.de/abfallkalender",
    "Next-Action": "40848818ae6d1b60fa948dee6d0b118e4ffa02f214",
    "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22abfallkalender%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fabfallkalender%22%2C%22refresh%22%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
    "x-deployment-id": "dpl_TcKadRcuPMzQdhBzzCCx5nQDCJjL",
    "Content-Type": "text/plain;charset=UTF-8",
    "Origin": "https://www.awista-kommunal.de",
    "Connection": "keep-alive",
    # "Sec-Fetch-Dest":"empty",
    # "Sec-Fetch-Mode":"cors",
    # "Sec-Fetch-Site":"same-origin",
}


data = '["Zeppenheim"]'
response = requests.post(
    url=url, headers=headers, data=data, allow_redirects=True
)
# response.encoding = response.apparent_encoding
print(response)
print(response.text)
# print(response.text)
# some parsing needed because the API returns type text/x-component and not a clean json object
# street_sug = json.loads(response.text[response.text.rfind("\n1:") + 3:])

# if len(street_sug["items"]) <= 1:
#     print("not enough input to parse for suggestions")
#     quit()
# if street_sug["noResultsMessage"] != "$undefined":
#     print(street_sug["noResultsMessage"])
# else:
#     for street in street_sug["items"]:
#         if street["id"] != "$undefined":
#             print("Calendar for " + street["title"] + ": ")
#             print(
#                 "https://awista-kommunal.de/abfallkalender/" + street["id"])
#             print("\n")
#             print("ICS endpoint for " + street["title"] + ": ")
#             print(
#                 "https://awista-kommunal.de/abfallkalender/"
#                 + street["id"]
#                 + "/calendar.ics"
#             )
#         else:
#             print(street["title"])
# print(street_sug["items"])
# print(street_sug["noResultsMessage"])
# print(street_sug)


# class Source:
#     def __init__(self, street: str):
#         self._street = street
#         self._ics = ICS

#     def fetch(self):
#         # entries = []

#         # entries.append(
#         #     Collection(
#         #         datetime.datetime(2020, 4, 11),
#         #         "Waste Type",
#         #     )
#         # )

#         response = requests.post(
#             url=url, headers=headers, data=street, allow_redirects=True
#         )
#         response.encoding = response.apparent_encoding

#         # some parsing needed because the API returns type text/x-component and not a clean json object
#         street_sug = json.loads(
#             response.text[response.text.rfind("\n1:") + 3:])

#         if len(street_sug["items"]) <= 1:
#             print("not enough input to parse for suggestions")
#             quit()
#         if street_sug["noResultsMessage"] != "$undefined":
#             print(street_sug["noResultsMessage"])
#         else:
#             for street in street_sug["items"]:
#                 if street["id"] != "$undefined":
#                     print("Calendar for " + street["title"] + ": ")
#                     print(
#                         "https://awista-kommunal.de/abfallkalender/" + street["id"])
#                     print("\n")
#                     print("ICS endpoint for " + street["title"] + ": ")
#                     print(
#                         "https://awista-kommunal.de/abfallkalender/"
#                         + street["id"]
#                         + "/calendar.ics"
#                     )
#                 else:
#                     print(street["title"])
#         # print(street_sug["items"])
#         # print(street_sug["noResultsMessage"])
#         # print(street_sug)

#         return

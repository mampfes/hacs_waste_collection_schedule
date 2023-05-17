import requests
from bs4 import BeautifulSoup
import dateutil.parser as parser
from waste_collection_schedule import Collection


TITLE = "Welwyn Hatfield Borough Council"
DESCRIPTION = "Source for www.welhat.gov.uk services for Welwyn Hatfield Borough Council, UK."
URL = "https://www.welhat.gov.uk"
TEST_CASES = {
    "test 1 - South Red": {"uprn": "100080965745", "postcode": "AL9 5EA"},
    "test 2 - Blue North": {"uprn": "100080977050", "postcode": "AL7 3ET"}
}

ICON_MAP = {
    "food": "mdi:apple",
    "garden": "mdi:tree",
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle"
}

class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        # Request #1 - obtain "__token" value
        url = 'https://www.welhat.gov.uk/xfp/form/214'
        response = requests.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find('form', action='/xfp/form/214')

        token = form.find('input', {'name': '__token'}).get('value')

        # Request #2 - retrieve next bin collection dates
        headers = {
            'Host': 'www.welhat.gov.uk',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://www.welhat.gov.uk',
            'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryuNcUUJl6BCDBZ9JO',
            'User-Agent': 'HAOS',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://www.welhat.gov.uk/xfp/form/214',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

        data = '------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="__token"\r\n\r\n' + token + '\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="page"\r\n\r\n492\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="locale"\r\n\r\nen_GB\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q9f451fe0ca70775687eeedd1e54b359e55f7c10c_0_0"\r\n\r\n' + self._postcode + '\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q9f451fe0ca70775687eeedd1e54b359e55f7c10c_1_0"\r\n\r\n' + self._uprn + '\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="qc3b0352c12fed5336c22352db2780a94ba369763"\r\n\r\nDomestic Waste Collection Service\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q17867a1a3aa5a53e67cceb42ae4c4fa70dade69d"\r\n\r\nGarden Waste Collection Service\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q0144c9059f13b2db9178a6c6fca02addc03829f5"\r\n\r\nDomestic Waste Sack Collection Service\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="qbaf6e9054b74213122e216f782a221f97eb98ce5"\r\n\r\nRecycling Collection Service\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q5176b7585f1db820bff96c617966eb586c4b8687"\r\n\r\nFood Waste Collection Service\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q90aa73493450c00b4651493354808f4e7cb26454"\r\n\r\nPM\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q73adcf07adf82c347e258dcce449ad7a6104e225"\r\n\r\n2023-05-10\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q8d79140ae1240f397891c65bd01c65e4c5003804"\r\n\r\n2023-05-06\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q5c1829b11ffbb34009248f4706ec98c9558b5e34"\r\n\r\n2023-05-13\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="q38f336d0c9beb90a6345002e6d913800fb4f04fa"\r\n\r\n\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO\r\nContent-Disposition: form-data; name="next"\r\n\r\nNext\r\n------WebKitFormBoundaryuNcUUJl6BCDBZ9JO--\r\n'

        response = requests.post('https://www.welhat.gov.uk/xfp/form/214', headers=headers, data=data)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.table
        entries = []

        for row in table.tbody.find_all('tr'):
            columns = row.find_all('td')
            collection = columns[0].text.strip()
            if collection == 'Food Waste Collection Service':
                collection = 'food'
            elif collection == 'Garden Waste Collection Service':
                collection = 'garden'
            elif collection == 'Recycling Collection Service':
                collection = 'recycling'
            elif collection == 'Domestic Waste Collection Service':
                collection = 'refuse'
            else:
                collection = 'unknown'
            date = columns[1].text.strip()
            date = parser.parse(date).date()
            entries.append(
                Collection(
                    date=date,
                    t=collection,
                    icon=ICON_MAP.get(collection)
                )
            )

        return entries
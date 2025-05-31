## Configuration via configuration.yaml

To configure the Shoalhaven City Council waste collection source, add the following to your `configuration.yaml` file under the `waste_collection_schedule` integration:

```
waste_collection_schedule:
    sources:
    - name: shoalhaven_nsw_gov_au
      args:
        geolocation_id: YOUR_GEOLOCATION_ID

```

## Configuration Variables

* **`geolocation_id`** (string) (required): Your unique Geolocation ID for the address. This is a long string of letters and numbers (e.g., `2ea7b0c7-b627-421d-8436-248b8da384b6`).

  **How to get your Geolocation ID:**

  1. Go to the Shoalhaven City Council 'My Area' page: <https://www.shoalhaven.nsw.gov.au/My-Area>

  2. Open Developer Tools in your browser by pressing F12 and go to the Network tab.

  3. Enter your address in the search bar and select it from the suggestions.

  4. Once your address information is displayed, look at the `wasteservices` URL in the Network tab.

  5. Copy the long string of letters and numbers that follows `geolocationid=` (e.g., `2ea7b0c7-b627-421d-8436-248b8da384b6`). This is your Geolocation ID.

## Example

```
waste_collection_schedule:
    sources:
    - name: shoalhaven_nsw_gov_au
      args:
        geolocation_id: "1ce23c4a-633a-464f-ab56-6f1d2c0d929f"


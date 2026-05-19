# South Lanarkshire Council, United Kingdom

Support for schedules provided by [South Lanarkshire Council](https://www.southlanarkshire.gov.uk), serving South Lanarkshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southlanarkshire_gov_uk
      args:
        record_id: DIRECTORY_RECORD_ID
        street_name: STREET_NAME_SLUG
        pdf_url: PDF_URL
```

### Configuration Variables

**record_id**
*(String | Integer) (required)*

The numeric directory record ID from your street's URL on the South Lanarkshire Council website (e.g. `574605`).

**street_name**
*(String) (required)*

The street name slug from your URL (e.g. `clincarthill_road_rutherglen`).

**pdf_url**
*(String) (required)*

Full URL to the council's bin collection calendar PDF for your area.

The integration combines the street webpage with the calendar PDF to build dated collections and keeps the council's published bin labels. It also checks the council's calendar index page and, when possible, refreshes this URL to the latest yearly PDF for the same calendar.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: southlanarkshire_gov_uk
      args:
        record_id: "574605"
        street_name: "clincarthill_road_rutherglen"
        pdf_url: "https://www.southlanarkshire.gov.uk/download/downloads/id/18301/east_kilbride_cambuslang_and_rutherglen_bin_collection_calendar_2026_-_households_with_4_bins.pdf"
```

## How to get the source arguments

### `record_id` and `street_name`

1. Go to <https://www.southlanarkshire.gov.uk> and search for your address using the bin collection lookup.
2. The URL of your street's collection page has the format:
   ```
   https://www.southlanarkshire.gov.uk/directory_record/574605/clincarthill_road_rutherglen
   ```
3. The number after `/directory_record/` is your **`record_id`** (e.g. `574605`).
4. The text after that is your **`street_name`** (e.g. `clincarthill_road_rutherglen`).

### `pdf_url`

1. Go to <https://www.southlanarkshire.gov.uk/downloads/download/791/bin_collection_calendars>.
2. Download the PDF for your area (e.g. *East Kilbride, Cambuslang and Rutherglen* or *Hamilton and Clydesdale*).
3. Copy the full URL of the PDF file — this is your **`pdf_url`**.

The PDF is required because it contains the dated collection schedule used by the source.

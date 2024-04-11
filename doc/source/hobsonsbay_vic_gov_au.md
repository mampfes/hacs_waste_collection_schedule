# Hobsons Bay City Council

Support for schedules provided by [Hobsons Bay City Council](https://www.hobsonsbay.vic.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hobsonsbay_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hobsonsbay_vic_gov_au
      args:
        street_address: 399 Queen St, Altona Meadows
```

## How to get the source arguments

Visit the [Hobsons Bay City Council: When will my bins be collected?](https://www.hobsonsbay.vic.gov.au/Services/Waste-Recycling/When-will-my-bins-be-collected) page to install the iOS or Android app, then search for your address. The `street_address` argument should exactly match the street address shown in the autocomplete result of the app. If you do not want to install the app, you can also use the [interactive waste collections map](https://hbcc.maps.arcgis.com/apps/webappviewer/index.html?id=4db29582f74b4ba2ab2152fedeefe7b1) to search for a supported address. However, note that it does not always match what the API expects.

# Liverpool City Council (NSW)

Support for schedules provided by [Liverpool City Council](https://www.liverpool.nsw.gov.au/) using their [Open Data Portal](https://data.liverpool.nsw.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: liverpool_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Your street address. Can be a partial address (e.g., "600 Kurrajong Road, Carnes Hill") - the source will search for matching addresses.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: liverpool_nsw_gov_au
      args:
        address: "600 Kurrajong Road, Carnes Hill"
```

## How to get the source arguments

Enter your street address. The source will search for matching addresses. When configuring via the UI, if multiple matches are found you'll be shown suggestions to choose from. Make sure your address is specific enough to return a single result.

**Note:** Addresses don't use abbreviations — use the full street type (e.g., "Road" not "Rd", "Avenue" not "Ave").

If you're having trouble finding your correctly formatted address, you can search the dataset directly at the [API console](https://data.liverpool.nsw.gov.au/explore/dataset/bin-collection-days/api/). In the `where` field, enter `gisaddress like "{search term}"`, for example `gisaddress like "600 Kurrajong Road"`.

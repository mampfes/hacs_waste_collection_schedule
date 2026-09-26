# Hobsons Bay City Council

Support for schedules provided by [Hobsons Bay City Council](https://www.hobsonsbay.vic.gov.au).

Source for Hobsons Bay City Council waste & recycling collection

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

Street number, street name and suburb as shown on the council's bin collection calendar, for example '399 Queen St, Altona Meadows'. The comma is optional.

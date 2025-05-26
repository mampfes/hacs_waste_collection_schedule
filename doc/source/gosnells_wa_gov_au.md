# City of Gosnells

Support for schedules provided by the [City of Gosnells](https://www.gosnells.wa.gov.au/Your_property/Rubbish_and_recycling/Find_your_waste_collection_dates), Western Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gosnells_wa_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gosnells_w_gov_au
      args:
        address: "15 Mackay Crescent GOSNELLS 6110"
```

## How to get the source arguments

Use the [City of Gosnells](https://www.gosnells.wa.gov.au/Your_property/Rubbish_and_recycling/Find_your_waste_collection_dates) website and search for your collection schedule. Use your address as it is displayed on the search results page.

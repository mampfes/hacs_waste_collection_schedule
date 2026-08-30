# City of Gosnells

Support for schedules provided by the [City of Gosnells](https://www.gosnells.wa.gov.au/City-Services/Waste-and-Recycling/Find-your-waste-collection-dates), Western Australia.

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

Your street address as it appears on the City of Gosnells website, e.g. `15 Mackay Crescent GOSNELLS 6110`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gosnells_wa_gov_au
      args:
        address: "15 Mackay Crescent GOSNELLS 6110"
```

## How to get the source arguments

Use the [City of Gosnells](https://www.gosnells.wa.gov.au/City-Services/Waste-and-Recycling/Find-your-waste-collection-dates) website and search for your collection schedule. Use your address as it is displayed on the search results page.

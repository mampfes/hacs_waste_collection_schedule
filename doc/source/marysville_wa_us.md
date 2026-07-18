# Marysville, WA

Support for schedules provided by [City of Marysville, WA Solid Waste & Recycling](https://marysvillewa.gov/172/Solid-Waste-Recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: marysville_wa_us
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**
*(string) (required)*

Your street address as house number and street name. Do not include city or ZIP code.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: marysville_wa_us
      args:
        street_address: 501 Delta Ave
```

## How to get the source arguments

Enter the house number and street name of your Marysville address — for example `501 Delta Ave` or `6400 88th St NE`. City and ZIP code are not needed.

This source returns **Garbage Collection** events based on the day-of-week schedule recorded in the city's ArcGIS feature service. Addresses with weekly pickup receive an entry every week; addresses flagged as monthly pickup receive an entry every four weeks (the database does not record which specific week of the month applies).

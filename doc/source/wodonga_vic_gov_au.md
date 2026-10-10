# City of Wodonga

Support for schedules provided by [City of Wodonga](https://www.wodonga.vic.gov.au).

Source for City of Wodonga (Victoria) kerbside collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wodonga_vic_gov_au
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
    - name: wodonga_vic_gov_au
      args:
        address: 104 Hovell St, Wodonga
```

## How to get the source arguments

Enter your street address in the City of Wodonga, e.g. '104 Hovell St, Wodonga'. Organics is collected weekly; Recycling and General Waste alternate fortnightly on the same day, as on the council's collection calendar at https://www.wodonga.vic.gov.au/Services/Recycling-and-Waste/Bins-and-Collection.

# City of Moreton Bay

Support for schedules provided by [City of Moreton Bay](https://www.moretonbay.qld.gov.au).

Source for City of Moreton Bay, Queensland, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moretonbay_qld_gov_au
      args:
        house_number: HOUSE_NUMBER
        street_name: STREET_NAME
        suburb: SUBURB
```

### Configuration Variables

**house_number**  
*(string) (required)*

**street_name**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: moretonbay_qld_gov_au
      args:
        house_number: '25'
        street_name: Pumicestone
        suburb: Bellara
```

## How to get the source arguments

Enter your house number, street name and suburb exactly as they appear on the City of Moreton Bay bin-day lookup at https://www.moretonbay.qld.gov.au/Services/Waste-Recycling/Collections/Bin-Days. The street name may be given with or without its street type (e.g. 'Pumicestone' or 'Pumicestone Street').

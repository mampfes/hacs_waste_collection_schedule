# City of Moreton Bay

Support for schedules provided by [City of Moreton Bay](https://www.moretonbay.qld.gov.au/), Queensland, Australia.

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
May be given with or without the street type, e.g. `Pumicestone` or `Pumicestone Street`.

**suburb**  
*(string) (required)*  
The suburb, e.g. `Bellara`. Required to disambiguate street names that appear in more than one suburb.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: moretonbay_qld_gov_au
      args:
        house_number: "25"
        street_name: Pumicestone
        suburb: Bellara
```

## How to get the source arguments

Enter your address at the [City of Moreton Bay bin-day lookup](https://www.moretonbay.qld.gov.au/Services/Waste-Recycling/Collections/Bin-Days) to confirm the exact street name and suburb. Then supply the house number, street name and suburb as the source arguments.

## Notes

General waste (red bin) is collected weekly. Recycling (yellow bin) and garden organics (lime green bin) are each collected fortnightly on the same weekday, on alternating weeks. Data is sourced from the council's public open-data feed (property waste collection days and recycle weeks).

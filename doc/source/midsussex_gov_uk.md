# Mid-Sussex District Council

Support for schedules provided by [Mid-Sussex District Council](https://www.midsussex.gov.uk/waste-recycling/bin-collection/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_name: NAME
        house_number: NUMBER
        street: STREET
        postcode: POSTCODE
```

### Configuration Variables

**house_name**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

If house_name is not provided then house_number becomes *(required)*

**street**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_name: Oaklands
        street: Oaklands Road
        postcode: RH16 1SS
```

```yaml
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_number: 6
        street: Withypitts
        postcode: RH10 4PJ
```

## How to get the source arguments

Search for your collection schedule on the address on the [Mid-Sussex District Council](https://www.midsussex.gov.uk/waste-recycling/bin-collection/) site to see how they format your address. General rule seems to be `HOUSE_NAME, HOUSE_NUMBER STREET POSTCODE` but how it can vary for multi-occupancy buildings etc, so you may need to adjust which parts of the address are used for each arg.
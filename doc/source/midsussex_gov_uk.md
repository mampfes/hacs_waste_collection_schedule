# Mid-Sussex District Council

Support for schedules provided by [Mid-Sussex District Council](https://www.midsussex.gov.uk/waste-recycling/bin-collection/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        address: ADDRESS
        house_name: NAME
        house_number: NUMBER
        street: STREET
        postcode: POSTCODE
```

### Configuration Variables

#### Preferred Method
**address**  
*(string) (required)*

The address as it appears on the midsussex.gov.uk website.

This is the preferred approach, if this is not used then the following legacy methods can be used.

#### Legacy Methods

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
# Preferred method
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        address: HAZELMERE REST HOME, 21 BOLNORE ROAD RH16 4AB
```

```yaml
# legacy method: house name, but no house number
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_name: Oaklands
        street: Oaklands Road
        postcode: RH16 1SS
```

```yaml
# legacy method: house number, but no house name
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_number: 6
        street: Withypitts
        postcode: RH10 4PJ
```

```yaml
# legacy method: house name used instead of house number
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_number: Lamedos
        street: Withypitts
        postcode: RH11 4XY
```
```yaml

# legacy method: house name and house number
waste_collection_schedule:
    sources:
    - name: midsussex_gov_uk
      args:
        house_name: Tireggub
        house_number: Lamedos
        street: Widdershins
        postcode: RH14 8BX
```

## How to get the source arguments

Search for your collection schedule on the address on the [Mid-Sussex District Council](https://www.midsussex.gov.uk/waste-recycling/bin-collection/) site to see how they format your address. Preferred approach is to copy the address as displayed. If that doesn't work, the individual components can be supplied. General rule seems to be `HOUSE_NAME, HOUSE_NUMBER STREET POSTCODE` but it can vary for multi-occupancy buildings, house names where there are no numbers,  house names where there are also house numbers, etc, so you may need to adjust which parts of the address are used for each arg.
# AMSA

Support for schedules provided by [AMSA](https://www.amsa.it/it/milano).

Source for AMSA (Milan, Italy) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: amsa_it
      args:
        address: ADDRESS
        house_number: HOUSE_NUMBER
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**house_number**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: amsa_it
      args:
        address: Via Monte Rosa
        house_number: '91'
        city: Milano
```

## How to get the source arguments

Provide the street name and house number of your address, as well as the city.

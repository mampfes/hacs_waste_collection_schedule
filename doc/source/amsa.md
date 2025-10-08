# AMSA

Support for schedules provided by [AMSA]("https://www.amsa.it/it/milano"), Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: amsa
      args:
        address: HOUSE_ADDRESS
        house_number: HOUSE_NUMBER
        city: CITY
```

## Configuration variables

**address**
*(string) (required)* : The address for your house.

**house_number**
*(string) (required)* : The house number for your house.

**city**
*(string) (optional)* : The city of your house, if needed specification, preferably in Italian.

Example:

```yaml
waste_collection_schedule:
    sources:
    - name: amsa
      args:
        address: "Viale Monte Rosa"
        house_number: "91"
        city: "Milano"
```

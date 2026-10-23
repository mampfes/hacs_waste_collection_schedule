# Pireva

Support for schedules provided by [Pireva](https://www.pireva.se).

Source for Pireva that serves Piteå kommun, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pireva_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pireva_se
      args:
        street_address: "Kolugnsv\xE4gen 1 R\xE4ddningstj\xE4nsten Mf"
```

## How to get the source arguments

Enter your address exactly as it is written in the address search on https://www.pireva.se/tomningsschema/ (street, number and, for some properties, a name, e.g. 'Kolugnsvägen 1 Räddningstjänsten Mf').

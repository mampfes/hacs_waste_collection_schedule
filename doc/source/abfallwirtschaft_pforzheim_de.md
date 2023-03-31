# Abfallwirtschaft Pforzheim

Support for schedules provided by [Abfallwirtschaft Pforzheim](https://www.abfallwirtschaft-pforzheim.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_pforzheim_de
      args:
        street: STREET
        house_number: HNR
        address_suffix: HNR_SUFFIX
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(integer) (required)*

**address_suffix**  
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_pforzheim_de
      args:
        street: "Eisenbahnstraße"
        house_number: 29
        address_suffix: "-33"
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on [https://www.abfallwirtschaft-pforzheim.de/kundenportal/abfallkalender](https://www.abfallwirtschaft-pforzheim.de/kundenportal/abfallkalender). Typos may result in an Exception. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.

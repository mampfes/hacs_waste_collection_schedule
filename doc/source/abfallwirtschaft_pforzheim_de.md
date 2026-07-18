# Abfallwirtschaft Pforzheim

Support for schedules provided by [Abfallwirtschaft Pforzheim](https://www.abfallwirtschaft-pforzheim.de).

Source for Abfallwirtschaft Pforzheim.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_pforzheim_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**address_suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_pforzheim_de
      args:
        street: "Abnobastra\xDFe"
        house_number: 3
        address_suffix: ''
```

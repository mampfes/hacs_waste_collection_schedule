# Landkreis Verden

Support for schedules provided by [Landkreis Verden](https://www.landkreis-verden.de/).

Source for Landkreis Verden waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_verden_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        house_number_addition: HOUSE_NUMBER_ADDITION
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_number_addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_verden_de
      args:
        city: Achim
        street: "Am Schie\xDFstand"
        house_number: 10
```

# RegioEntsorgung Städteregion Aachen

Support for schedules provided by [RegioEntsorgung Städteregion Aachen](https://regioentsorgung.de).

RegioEntsorgung Städteregion Aachen

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: regioentsorgung_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: regioentsorgung_de
      args:
        city: "W\xFCrselen"
        street: "Merzbr\xFCck"
        house_number: 200
```

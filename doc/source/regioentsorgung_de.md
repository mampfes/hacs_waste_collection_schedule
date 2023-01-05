# RegioEntsorgung

Support for schedules provided by [RegioEntsorgung](https://regioentsorgung.de/) located near Aachen, Germany.

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
*(string | number) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: regioentsorgung_de
      args:
        city: Würselen
        street: Merzbrück
        house_number: 200
```

## How to get the source arguments

Go to <https://regioentsorgung.de/service/abfallkalender/>, to get the correct values for the three address arguments.

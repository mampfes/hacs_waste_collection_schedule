# Mannheim.de 

Support for schedules provided by [Mannheim.de](https://www.mannheim.de/de/service-bieten/umwelt/stadtraumservice-mannheim/abfallwirtschaft/abfallkalender/abfallkalender-online).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mannheim_de
      args:
        f_id_location: LocationID
```

### Configuration Variables

**f_id_location**  
*(integer) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mannheim_de
      args:
        f_id_location: 454013
```

## How to get the source arguments

### Extract arguments from website

1. Open the digital abfallkalender for Mannheim [https://www.insert-it.de/BmsAbfallkalenderMannheim](https://www.insert-it.de/BmsAbfallkalenderMannheim).
2. Enter the street name and the number
3. Check the browsers address bar and copy the bmsLocationId argument. Use this id in the configuration as `f_id_location`.

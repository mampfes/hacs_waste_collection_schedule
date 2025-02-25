# Landkreis Neumarkt

Support for schedules provided by [Landkreis Neumarkt](https://www.abfuhrplan-landkreis-neumarkt.de), serving Landkreis Neumarkt, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfuhrplan_landkreis_neumarkt
      args:
        city: CITY (Gmeinde/Ort)
        street: STREET (Straße)
        
```

### Configuration Variables

**city**  
*(String) (required)*
**street**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfuhrplan_landkreis_neumarkt
      args:
        city: dietfurt
        street: industriestrasse
        
```

## How to get the source argument

Find the parameter of your address using [https://www.abfuhrplan-landkreis-neumarkt.de](https://www.abfuhrplan-landkreis-neumarkt.de) and write them exactly like on the web page.

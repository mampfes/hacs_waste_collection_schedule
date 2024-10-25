# Landkreis Neumarkt

Support for schedules provided by [Schwabach](https://www.abfuhrplan-schwabach.de/), serving the city of Schwabach, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfuhrplan_schwabach_de
      args:
        street: STREET (Straße)
```

### Configuration Variables

**street**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfuhrplan_schwabach_de
      args:
        street: Am Alten Friedhof 3, 3a        
```

## How to get the source argument

Find the parameter of your address using [https://www.abfuhrplan-schwabach.de/](https://www.abfuhrplan-schwabach.de/) and write them exactly like on the web page.

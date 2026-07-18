# Landkreis Neumarkt

Support for schedules provided by [Landkreis Neumarkt](https://www.abfuhrplan-landkreis-neumarkt.de).

Source for Landkreis Neumarkt.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfuhrplan_landkreis_neumarkt_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfuhrplan_landkreis_neumarkt_de
      args:
        city: dietfurt
        street: industriestrasse
```

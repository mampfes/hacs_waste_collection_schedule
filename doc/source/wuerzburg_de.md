# Abfallkalender Würzburg (deprecated)

Support for schedules provided by [Abfallkalender Würzburg (deprecated)](https://www.wuerzburg.de).

Deprecated: Use the ICS source instead. Source for waste collection in the city of Würzburg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wuerzburg_de
      args:
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**district**  
*(string) (optional)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wuerzburg_de
      args:
        district: Altstadt
```

## How to get the source arguments

This source remains deprecated; the generic ICS configuration is recommended. Enter district or street exactly as listed on the city calendar. Street takes precedence if both are set. The published event API supplies actual dates and collection pictures. Types now use canonical, localised names; update filters and customisations using old labels.

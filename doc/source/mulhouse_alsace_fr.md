# Mulhouse Alsace Agglomération (m2A)

Support for schedules provided by [Mulhouse Alsace Agglomération (m2A)](https://data.mulhouse-alsace.fr/).

Source for door-to-door household waste collection in the Mulhouse Alsace Agglomération (m2A), based on its open data portal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mulhouse_alsace_fr
      args:
        commune: COMMUNE
        quartier: QUARTIER
```

### Configuration Variables

**commune**  
*(string) (required)*

**quartier**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mulhouse_alsace_fr
      args:
        commune: Wittelsheim
```

## How to get the source arguments

Provide your municipality; for Mulhouse also provide the district.

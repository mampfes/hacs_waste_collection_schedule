# Marktgemeinde Eggelsberg

Support for schedules provided by [Marktgemeinde Eggelsberg](https://www.eggelsberg.at).

Source for Marktgemeinde Eggelsberg waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eggelsberg_at
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eggelsberg_at
      args:
        zone: A
```

## How to get the source arguments

Select your zone (A or B). This determines your Bioabfall (organic waste) collection schedule. All other waste types apply to all zones.

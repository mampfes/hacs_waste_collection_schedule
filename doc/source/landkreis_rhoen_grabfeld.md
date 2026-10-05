# Landkreis Rhön Grabfeld

Support for schedules provided by [Landkreis Rhön Grabfeld](https://www.abfallinfo-rhoen-grabfeld.de/).

Source for Landkreis Rhön Grabfeld in Germany. Uses service by offizium.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_rhoen_grabfeld
      args:
        city: CITY
        district: DISTRICT
```

### Configuration Variables

**city**  
*(string) (optional)*

**district**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_rhoen_grabfeld
      args:
        city: Ostheim
```

## How to get the source arguments

Enter the municipality (`city`) and/or the village (`district`) exactly as listed on https://www.abfallinfo-rhoen-grabfeld.de/. Leave both empty to get the collections of the whole district.

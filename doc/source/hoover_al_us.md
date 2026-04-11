# Hoover, AL

Support for schedules provided by [Hoover, AL](https://hooveralabama.gov/559/Pickup-Schedule).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hoover_al_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hoover_al_us
      args:
        address: 2255 Tyler Rd, Hoover, AL
```

## How to get the source arguments

Visit the [Hoover Garbage Pickup Schedule](https://hooveralabama.maps.arcgis.com/apps/webappviewer/index.html?id=57a076197eca4060b566ad6ed4abc3f0) page and search for your address. Use your full street address including city and state (e.g. "2255 Tyler Rd, Hoover, AL").

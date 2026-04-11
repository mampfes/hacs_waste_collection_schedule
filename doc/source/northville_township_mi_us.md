# Northville Township, MI

Support for schedules provided by [Northville Township, MI](https://www.twp.northville.mi.us/services/public-services/solid-waste-collection-recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northville_township_mi_us
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
    - name: northville_township_mi_us
      args:
        address: 16795 Northville Rd
```

## How to get the source arguments

Visit the [Northville Township Collection Schedule](https://www.arcgis.com/apps/webappviewer/index.html?id=ea82cac1dac745518c87a2ed45825460) page and search for your address. Use the street number and street name (e.g. "16795 Northville Rd"). Note that numbered mile roads should use the number form (e.g. "6 Mile" not "Six Mile").

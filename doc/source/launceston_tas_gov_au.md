# Launceston City Council

Support for schedules provided by [Launceston City Council](https://www.launceston.tas.gov.au/Natural-Environment-and-Waste/Kerbside-Collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: launceston_tas_gov_au
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
    - name: launceston_tas_gov_au
      args:
        address: 40 Southgate Dr, Kings Meadows, TAS
```

## How to get the source arguments

Visit the [Launceston Kerbside Collection Pickup Days](https://launceston.maps.arcgis.com/apps/webappviewer/index.html?id=7a89f9862a0846bd9af0a538f5194a55) page and search for your address. Use your full street address including suburb and state (e.g. "40 Southgate Dr, Kings Meadows, TAS").

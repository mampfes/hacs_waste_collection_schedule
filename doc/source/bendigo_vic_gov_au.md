# City of Greater Bendigo

Support for schedules provided by [City of Greater Bendigo](https://www.bendigo.vic.gov.au).

Source for City of Greater Bendigo rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bendigo_vic_gov_au
      args:
        latitude: LATITUDE
        longitude: LONGITUDE
```

### Configuration Variables

**latitude**  
*(float) (required)*

**longitude**  
*(float) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bendigo_vic_gov_au
      args:
        latitude: -36.701755710607394
        longitude: 144.31310883736967
```

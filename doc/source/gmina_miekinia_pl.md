# Gmina Miękinia

Support for schedules provided by [Gmina Miękinia](https://api.skycms.com.pl).

Source for Gmina Miękinia, Poland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_miekinia_pl
      args:
        location_id: LOCATION_ID
```

### Configuration Variables

**location_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_miekinia_pl
      args:
        location_id: 8
```

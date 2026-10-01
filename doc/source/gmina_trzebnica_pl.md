# Gmina Trzebnica

Support for schedules provided by [Gmina Trzebnica](https://trzebnica.pl).

Source for Gmina Trzebnica, Poland (SkyCMS municipal app API)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_trzebnica_pl
      args:
        region_id: REGION_ID
```

### Configuration Variables

**region_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_trzebnica_pl
      args:
        region_id: 88
```

## How to get the source arguments

Install the 'Gmina Trzebnica' app and look up your waste collection region. The region ID can be found in the app's waste calendar section, or in the region list linked from the documentation of this source.

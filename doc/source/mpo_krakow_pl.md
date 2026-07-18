# MPO Kraków

Support for schedules provided by [MPO Kraków](https://harmonogram.mpo.krakow.pl/).

Source script for MPO Kraków

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mpo_krakow_pl
      args:
        street_name: STREET_NAME
        building_number: BUILDING_NUMBER
```

### Configuration Variables

**street_name**  
*(string) (required)*

**building_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mpo_krakow_pl
      args:
        street_name: Romanowicza
        building_number: 1 DM
```

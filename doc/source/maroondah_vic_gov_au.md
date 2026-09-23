# Maroondah City Council

Support for schedules provided by [Maroondah City Council](https://www.maroondah.vic.gov.au).

Source for Maroondah City Council. Finds both green waste and general recycling dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maroondah_vic_gov_au
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
    - name: maroondah_vic_gov_au
      args:
        address: 1 Abbey Court, RINGWOOD 3134
```

# Horowhenua District Council

Support for schedules provided by [Horowhenua District Council](https://www.horowhenua.govt.nz/).

Source for Horowhenua District Council Rubbish & Recycling collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: horowhenua_govt_nz
      args:
        street_name: STREET_NAME
        street_number: STREET_NUMBER
        post_code: POST_CODE
        town: TOWN
```

### Configuration Variables

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

**post_code**  
*(string) (required)*

**town**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: horowhenua_govt_nz
      args:
        post_code: '4821'
        town: Shannon
        street_name: Bryce Street
        street_number: '55'
```

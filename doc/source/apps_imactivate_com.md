# Apps by imactivate

Support for schedules provided by [Apps by imactivate](https://imactivate.com/).

Source for Apps by imactivate.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: apps_imactivate_com
      args:
        street: STREET
        number: NUMBER
        postcode: POSTCODE
        town: TOWN
```

### Configuration Variables

**street**  
*(string) (required)*

**number**  
*(string) (required)*

**postcode**  
*(string) (required)*

**town**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: apps_imactivate_com
      args:
        postcode: LS62SE
        town: Leeds
        street: sharp mews
        number: 2
```

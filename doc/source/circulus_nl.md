# Circulus

Support for schedules provided by [Circulus.nl](https://www.circulus.nl/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: circulus_nl
      args:
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables
**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
   - name: circulus_nl
      args:
        post_code: 7206AC
        house_number: 1
```

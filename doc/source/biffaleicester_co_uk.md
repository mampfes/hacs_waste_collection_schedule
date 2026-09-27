# Leicester City Council

Support for schedules provided by [Leicester City Council](https://www.leicester.gov.uk).

Source for city of Leicester, UK.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: biffaleicester_co_uk
      args:
        uprn: UPRN
```

### Using post_code and number

```yaml
waste_collection_schedule:
  sources:
    - name: biffaleicester_co_uk
      args:
        post_code: POST_CODE
        number: NUMBER
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**post_code**  
*(string) (alternative)*

**number**  
*(string) (alternative)*

Provide one of: `uprn` or `post_code` + `number`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: biffaleicester_co_uk
      args:
        uprn: 002465020938
```

### Using post_code and number

```yaml
waste_collection_schedule:
  sources:
    - name: biffaleicester_co_uk
      args:
        post_code: LE5 5QD
        number: '30'
```

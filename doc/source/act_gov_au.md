# Australian Capital Territory (ACT)

Support for schedules provided by [Australian Capital Territory (ACT)](https://www.cityservices.act.gov.au/recycling-and-waste).

Source script for Australian Capital Territory (ACT).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: SUBURB
        split_suburb: SPLIT_SUBURB
```

### Configuration Variables

**suburb**  
*(string) (required)*

**split_suburb**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: Bruce
```

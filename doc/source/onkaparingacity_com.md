# City of Onkaparinga Council

Support for schedules provided by [City of Onkaparinga Council](https://www.onkaparingacity.com/).

Source for City of Onkaparinga Council, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: onkaparingacity_com
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
    - name: onkaparingacity_com
      args:
        address: 18 Flagstaff Road, FLAGSTAFF HILL 5159
```

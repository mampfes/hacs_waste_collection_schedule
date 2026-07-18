# Greater Dandenong City Council

Support for schedules provided by [Greater Dandenong City Council](https://www.greaterdandenong.vic.gov.au).

Source for greaterdandenong.vic.gov.au waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: greaterdandenong_vic_gov_au
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
    - name: greaterdandenong_vic_gov_au
      args:
        address: 45 Ardgower Road Noble Park
```

## How to get the source arguments

Enter your address as it appears on the <a href='https://www.greaterdandenong.vic.gov.au/find-my-bin-day'>Find My Bin Day</a> page.

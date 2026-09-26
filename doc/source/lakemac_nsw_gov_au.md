# Lake Macquarie City Council

Support for schedules provided by [Lake Macquarie City Council](https://www.lakemac.com.au/).

Source for Lake Macquarie City Council, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lakemac_nsw_gov_au
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
    - name: lakemac_nsw_gov_au
      args:
        address: 386 Pacific Highway, MURRAYS BEACH NSW 2281
```

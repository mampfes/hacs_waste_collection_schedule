# Western Bay of Plenty District Council

Support for schedules provided by [Western Bay of Plenty District Council](https://kerbsidecollective.co.nz/).

Source script for Western Bay of Plenty District Council kerbside collections via kerbsidecollective.co.nz

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: western_bay_of_plenty_nz
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
    - name: western_bay_of_plenty_nz
      args:
        address: 15 Seaview Road
```

## How to get the source arguments

Enter your street address as it appears on kerbsidecollective.co.nz, e.g. '15 Seaview Road'.

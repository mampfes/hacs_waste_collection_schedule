# Waikato District Council

Support for schedules provided by [Waikato District Council](https://www.waikatodistrict.govt.nz/).

Source for Waikato District Council kerbside rubbish and recycling collection, New Zealand.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: waikato_district_council_govt_nz
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
    - name: waikato_district_council_govt_nz
      args:
        address: 42B Mahuta Station Road, Rotowaro
```

## How to get the source arguments

Enter your address as it appears on the council's rubbish and recycling collection page, e.g. '18 Example Drive, Huntly'. If the address cannot be found uniquely, the error message will list the closest matches known to the council.

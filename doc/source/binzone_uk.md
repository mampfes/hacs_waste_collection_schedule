# BinDay (South & Vale)

Support for schedules provided by [BinDay (South & Vale)](https://www.southoxon.gov.uk/).

Consolidated source for waste collection services from:
        South Oxfordshire District Council
        Vale of White Horse District Council
        

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: binzone_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: binzone_uk
      args:
        uprn: '100120903018'
```

## How to get the source arguments

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

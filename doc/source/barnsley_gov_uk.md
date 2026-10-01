# Barnsley Metropolitan Borough Council

Support for schedules provided by [Barnsley Metropolitan Borough Council](https://barnsley.gov.uk).

Source for Barnsley Metropolitan Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: barnsley_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: barnsley_gov_uk
      args:
        postcode: S71 1EE
        uprn: 100050671689
```

## How to get the source arguments

Enter your postcode and your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)).

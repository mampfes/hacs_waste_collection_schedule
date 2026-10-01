# Hinckley & Bosworth Borough Council

Support for schedules provided by [Hinckley & Bosworth Borough Council](https://www.hinckley-bosworth.gov.uk).

Source for Hinckley & Bosworth Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hinckley_bosworth_gov_uk
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
    - name: hinckley_bosworth_gov_uk
      args:
        uprn: '100030499851'
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).

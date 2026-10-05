# FCC Environment

Support for schedules provided by [FCC Environment](https://fccenvironment.co.uk).

Consolidated source for waste collection services for ~60 local authorities. Currently supports: West Devon (Generic Provider), South Hams (Generic Provider), Market Harborough (Custom Provider)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fccenvironment_co_uk
      args:
        uprn: UPRN
        region: REGION
```

### Configuration Variables

**uprn**  
*(string) (required)*

**region**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fccenvironment_co_uk
      args:
        uprn: '100030491624'
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and choose your council as the region (harborough, southhams or westdevon; Harborough is the default).

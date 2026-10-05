# Stockport Council

Support for schedules provided by [Stockport Council](https://stockport.gov.uk).

Source for bin collection services for Stockport Council, UK.
 Refactored with thanks from the Manchester equivalent

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stockport_gov_uk
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
    - name: stockport_gov_uk
      args:
        uprn: '100011460157'
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).

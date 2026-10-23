# Manchester City Council

Support for schedules provided by [Manchester City Council](https://www.manchester.gov.uk).

Source for bin collection services for Manchester City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: manchester_uk
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
    - name: manchester_uk
      args:
        uprn: '77065560'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/.

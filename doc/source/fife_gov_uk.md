# Fife Council

Support for schedules provided by [Fife Council](https://www.fife.gov.uk).

Source for Fife Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fife_gov_uk
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
    - name: fife_gov_uk
      args:
        uprn: 320069186
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/.

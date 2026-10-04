# Stroud District Council

Support for schedules provided by [Stroud District Council](https://stroud.gov.uk).

Source for Stroud District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stroud_gov_uk
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
    - name: stroud_gov_uk
      args:
        postcode: GL6 9BW
        uprn: 100120517945
```

## How to get the source arguments

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument. You can find your UPRN at https://www.findmyaddress.co.uk/.

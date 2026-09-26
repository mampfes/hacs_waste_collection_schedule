# Staffordshire Moorlands District Council

Support for schedules provided by [Staffordshire Moorlands District Council](https://www.staffsmoorlands.gov.uk).

Source for waste collection services for Staffordshire Moorlands District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: staffsmoorlands_gov_uk
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
    - name: staffsmoorlands_gov_uk
      args:
        postcode: ST8 7EA
        uprn: '10010602737'
```

## How to get the source arguments

Your UPRN can be found by searching your postcode at https://www.staffsmoorlands.gov.uk/findyourbinday (which redirects to the council's Public Dashboard) and selecting your address. The value shown in the address dropdown is your UPRN. Alternatively, find your UPRN at https://www.findmyaddress.co.uk/

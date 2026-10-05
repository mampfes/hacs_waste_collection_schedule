# Mid and East Antrim

Support for schedules provided by [Mid and East Antrim](https://www.midandeastantrim.gov.uk).

Source for Mid and East Antrim Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midandeastantrim_gov_uk
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
    - name: midandeastantrim_gov_uk
      args:
        uprn: 185438838
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.

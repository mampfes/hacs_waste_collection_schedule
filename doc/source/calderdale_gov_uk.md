# Calderdale Council

Support for schedules provided by [Calderdale Council](https://www.calderdale.gov.uk).

Source for calderdale.gov.uk services for Calderdale Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: calderdale_gov_uk
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
    - name: calderdale_gov_uk
      args:
        postcode: OL14 7BX
        uprn: 010010152783
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details. Leading zeros may be left out.

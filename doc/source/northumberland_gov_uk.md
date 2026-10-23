# Northumberland County Council

Support for schedules provided by [Northumberland County Council](https://www.northumberland.gov.uk).

Source for Northumberland County Council waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northumberland_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: northumberland_gov_uk
      args:
        uprn: '100110637553'
        postcode: NE46 1UF
```

## How to get the source arguments

Visit https://bincollection.northumberland.gov.uk/postcode, enter your postcode and select your address. The UPRN is the number in the address dropdown (or find it at https://www.findmyaddress.co.uk/).

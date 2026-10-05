# Tameside Metropolitan Borough Council

Support for schedules provided by [Tameside Metropolitan Borough Council](https://www.tameside.gov.uk).

Source for tameside.gov.uk, Tameside Metropolitan Borough Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tameside_gov_uk
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
    - name: tameside_gov_uk
      args:
        postcode: M34 6AG
        uprn: '100011601683'
```

## How to get the source arguments

Enter your postcode and your UPRN, which you can find at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).

# Midlothian Council

Support for schedules provided by [Midlothian Council](https://my.midlothian.gov.uk/).

Source script for my.midlothian.gov.uk bin collections

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midlothian_gov_uk
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
    - name: midlothian_gov_uk
      args:
        uprn: '120001401'
        postcode: EH26 8AG
```

## How to get the source arguments

Find your UPRN and postcode from your council documents or invoices.

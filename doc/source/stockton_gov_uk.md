# Stockton-on-Tees Borough Council

Support for schedules provided by [Stockton-on-Tees Borough Council](https://www.stockton.gov.uk/).

Source for Stockton-on-Tees Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stockton_gov_uk
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
    - name: stockton_gov_uk
      args:
        uprn: '100110203615'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by entering your address. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

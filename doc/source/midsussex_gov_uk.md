# Mid Sussex District Council (Whitespace WRP)

Support for schedules provided by [Mid Sussex District Council (Whitespace WRP)](https://www.midsussex.gov.uk/waste-and-recycling/).

Source script for midsussex.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midsussex_gov_uk
      args:
        postcode: POSTCODE
        street: STREET
        number: NUMBER
```

### Configuration Variables

**postcode**  
*(string) (required)*

**street**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: midsussex_gov_uk
      args:
        number: '23'
        street: HIGH STREET
        postcode: RH17 6TB
```

## How to get the source arguments

Enter your property's postcode, street name and house name or number (or business name) as they appear in the council's collection search. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels. The old `house_number` argument is gone; use `number` instead.

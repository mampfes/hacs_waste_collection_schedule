# Hastings Borough Council

Support for schedules provided by [Hastings Borough Council](https://www.hastings.gov.uk/).

Source for hastings.gov.uk services for Hastings Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hastings_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hastings_gov_uk
      args:
        postcode: TN34 1QF
        house_number: 36
        uprn: 100060038877
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering your address details. Leave postcode and house_number empty: they are no longer used. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.

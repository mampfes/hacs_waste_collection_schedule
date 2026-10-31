# Swansea Council

Support for schedules provided by [Swansea Council](https://swansea.gov.uk).

Source script for swansea.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: swansea_gov_uk
      args:
        post_code: POST_CODE
        street_name: STREET_NAME
        uprn: UPRN
```

### Configuration Variables

**post_code**  
*(string) (required)*

**street_name**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: swansea_gov_uk
      args:
        street_name: cwmdonkin
        post_code: SA20RA
```

## How to get the source arguments

Enter the full postcode of your property. Collections are scheduled per street, so that is usually enough; to pick one address, also enter part of it (e.g. the street name) or its Unique Property Reference Number (UPRN). Since the v3 pipeline migration, the pink and green collection weeks are reported as the waste types collected in them (as listed for your address), using canonical, localised names. Update filters, automations and customisations using the old labels.

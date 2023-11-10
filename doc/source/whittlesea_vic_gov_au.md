# Whittlesea Council (VIC)

Support for schedules provided by [Whittlesea Council (VIC)](https://whittlesea.vic.gov.au/community-support/my-neighbourhood/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: whittlesea_vic_gov_au
      args:
        street_number: STREET_NUMBER
        suburb: SUBURB
        street_name: STREET_NAME
        postcode: POSTCODE
```

### Configuration Variables

**street_number**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**suburb**<br>
*(string) (required)*

**postcode**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: whittlesea_vic_gov_au
      args:
        street_number: '25'
        street_name: Ferres Bouleavard
        suburb: South Morang
        postcode: '3752'
```

## How to get the source arguments

Visit the [Whittlesea Council (VIC)](https://whittlesea.vic.gov.au/community-support/my-neighbourhood/) page and search for your address.  The arguments should exactly match the results shown.

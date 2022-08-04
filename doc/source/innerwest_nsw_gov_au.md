# Inner West Council (NSW)

Support for schedules provided by [Inner West Council (NSW)](https://www.innerwest.nsw.gov.au/live/waste-and-recycling/bins-and-clean-ups/waste-calendar).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: innerwest_nsw_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**street_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: innerwest_nsw_gov_au
      args:
        suburb: Tempe
        street_name: Princess Hwy
        street_number: 800
```

## How to get the source arguments

Visit the [Inner West Council (NSW)](https://www.innerwest.nsw.gov.au/live/waste-and-recycling/bins-and-clean-ups/waste-calendar) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property.

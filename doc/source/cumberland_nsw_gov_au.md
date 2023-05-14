# Inner West Council (NSW)

Support for schedules provided by [Cumberland Council (NSW)](https://www.cumberland.nsw.gov.au/find-your-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cumberland_nsw_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cumberland_nsw_gov_au
      args:
        suburb: Berala
        street_name: Woodburn Road
        street_number: 98 to 104
```

## How to get the source arguments

Visit the [Cumberland Council (NSW)](https://www.cumberland.nsw.gov.au/find-your-bin-day) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property.

# Hawkesbury City Council

Support for schedules provided by [Hawkesbury City Council](https://www.hawkesbury.nsw.gov.au/), serving the Hawkesbury council in NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hawkesbury_nsw_gov_au
      args:
        suburb: SUBURB
        street: STREET
        houseNo: HOUSENO
        postCode: POSTCODE
```
### Configuration Variables

**suburb**  
*(string) (required)*

**street**  
*(string) (required)*

**houseNo**  
*(string) (required)*

**postCode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hawkesbury_nsw_gov_au
      args:
        suburb: South Windsor
        street: George Street
        houseNo: 539
        postCode: 2756
```

## How to get the source arguments

The source arguments are simply the values of the 3 selections from the web form.

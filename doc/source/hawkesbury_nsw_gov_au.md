# The Hawkesbury City Council, Sydney

Support for schedules provided by [The Hawkesbury City Council, Sydney](https://www.hawkesbury.nsw.gov.au/).

Source for Hawkesbury City Council, Sydney, Australia waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hawkesbury_nsw_gov_au
      args:
        suburb: SUBURB
        street: STREET
        postCode: POSTCODE
        houseNo: HOUSENO
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street**  
*(string) (required)*

**postCode**  
*(string) (required)*

**houseNo**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hawkesbury_nsw_gov_au
      args:
        suburb: south windsor
        street: George Street
        houseNo: 539
        postCode: 2756
```

## How to get the source arguments

Enter the suburb, street name (abbreviations such as 'St' or 'Rd' are expanded), house number and postcode of your property.

# The Hills, Sydney's Garden Shire

Support for schedules provided by [The Hills Council](https://www.thehills.nsw.gov.au/Home), serving the city of Sydney, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: thehills_nsw_gov_au
      args:
        suburb: SUBURB
        street: STREET
        houseNo: HOUSENO
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street**  
*(string) (required)*

**houseNo**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: thehills_nsw_gov_au
      args:
        suburb: ANNANGROVE
        street: Amanda Place
        houseNo: 10
```

## How to get the source arguments

The source arguments are simply the values of the 3 selections from the web form.

# The Hills Shire Council, Sydney

Support for schedules provided by [The Hills Shire Council, Sydney](https://www.thehills.nsw.gov.au/).

Source for Hills Shire Council, Sydney, Australia waste collection.

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

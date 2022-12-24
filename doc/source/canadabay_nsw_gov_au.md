# City of Canada Bay Council

Support for schedules provided by [City of Canada Bay Council](https://www.canadabay.nsw.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: canadabay_nsw_gov_au
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
    - name: canadabay_nsw_gov_au
      args:
        suburb: Mortlake
        street_name: Tennyson Road
        street_number: 76
```

## How to get the source arguments

Visit the [City of Canada Bay Council bin collection calendar](https://www.canadabay.nsw.gov.au/residents/waste-and-recycling/my-bins/my-bin-collection) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property.

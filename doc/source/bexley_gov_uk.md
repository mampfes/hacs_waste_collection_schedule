# London Borough of Bexley

Support for schedules provided by the [London Borough of Bexley](https://waste.bexley.gov.uk/waste), serving the London Borough of Bexley, UK. 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        uprn: PROPERTY_ID
```

### Configuration Variables

**property**<br>
*(string) (required)*

Unique number the  London Borough of Bexley uses to identify your property.

#### How to find your `PROPERTY_ID`
Search for your waste collection schedule at (https://waste.bexley.gov.uk/waste/). Your `PROPERTY_ID` is the set of numbers at the end of the url when your schedule is being displayed.

For example: waste.bexley.gov.uk/waste/`6296702`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        property: "100020254340"
```


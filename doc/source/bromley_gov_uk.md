# London Borough of Bromley

Support for schedules provided by the [London Borough of Bromley](https://bromely.gov.uk), serving Bromley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bromley_gov_uk
      args:
        property: PROPERTY_ID
```

### Configuration Variables

### Configuration Variables

**property**<br>
*(string) (required)*

Unique number the  London Borough of Bromley uses to identify your property.


#### How to find your `PROPERTY_ID`
Serach for your waste collection schedule at (https://recyclingservices.bromley.gov.uk/waste/). Your `PROPERTY_ID` is the set of numbers at the end of the url when your schedule is being displayed.

For example: recyclingservices.bromley.gov.uk/waste/`6296702`

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: bromley_gov_uk
      args:
        property: 6296702
```
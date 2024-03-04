# London Borough of Newham

Support for schedules provided by the [London Borough of Newham](https://www.newham.gov.uk), serving Newham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: newham_gov_uk
      args:
        property: PROPERTY_ID
```

### Configuration Variables

**property**<br>
*(string) (required)*

Unique number the London Borough of Newham uses to identify your property.


#### How to find your `PROPERTY_ID`

Searach for your waste collection schedule at (https://bincollection.newham.gov.uk/). Your `PROPERTY_ID` is the set of numbers at the end of the url when your schedule is being displayed.

For example: https://bincollection.newham.gov.uk/Details/Index/000046029438

You can also find your `PROPERTY_ID`/`UPRN` by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: newham_gov_uk
      args:
        property: "000046029438"
```

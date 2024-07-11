# Newark & Sherwood District Council

Support for schedules provided by [Newark & Sherwood District Council](https://app.newark-sherwooddc.gov.uk/bincollection/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: newark_sherwooddc_gov_uk
          args:
              uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
_(string) (required)_

Unique number the council uses to identify your property.

#### How to find your `UPRN`

Serach for your waste collection schedule at (https://app.newark-sherwooddc.gov.uk/bincollection/). Your `UPRN` is the set of numbers at the end of the url when your schedule is being displayed.

For example: https://app.newark-sherwooddc.gov.uk/bincollection/calendar?pid=`010091745473`

_Note:_ You can ignore the `Address` parameter, it's optional.

## Example

```yaml
waste_collection_schedule:
    sources:
        - name: newark_sherwooddc_gov_uk
          args:
              uprn: '010091745473'
```

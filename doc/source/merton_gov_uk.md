# London Borough of Merton

Support for schedules provided by the [London Borough of Merton](https://merton.gov.uk), serving Merton, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: merton_gov_uk
      args:
        property: PROPERTY_ID
```

### Configuration Variables

**property**<br>
_(string) (required)_

Unique number the London Borough of Merton uses to identify your property.

#### How to find your `PROPERTY_ID`

Serach for your waste collection schedule at (https://myneighbourhood.merton.gov.uk/Wasteservices/WasteServicesSearch.aspx). Your `PROPERTY_ID` is the set of numbers at the end of the url when your schedule is being displayed.

For example: myneighbourhood.merton.gov.uk/Wasteservices/WasteServices.aspx?ID=`28166109`

_Note:_ You can ignore the `Address` parameter, it's optional.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: merton_gov_uk
      args:
        property: 28166109
```

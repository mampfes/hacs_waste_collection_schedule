# City of Oklahoma City

Support for schedules provided by [City of Oklahoma City](https://www.okc.gov/), serving City of Oklahoma City.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: okc.gov
      args:
        objectID: UNIQUE_PROPERTY_IDENTIFIER
```

### Configuration Variables

**objectID**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: okc.gov
      args:
        objectID: "1781151"
```

## How to find your `objectID`

Using a browser, go to [data.okc.gov](https://data.okc.gov/portal/page/viewer?datasetName=Address%20Trash%20Services).
Click on the `Map` tab, search for your address, then click on your house. Your schedule will be displayed.
Click on the `Table` tab, then click on the `Filter By Map` menu item, and click `Apply` to reduce the number of items being displayed. Note: In the previous step, the more you zoom in on your house, the better this filter works.
Find your address in the filtered list and make a note of the `Object ID` number in the first column. This is the number you need to use.

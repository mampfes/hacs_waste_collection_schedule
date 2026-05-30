# Castle Point Borough Council

Support for schedules provided by [Castle Point Borough Council](https://www.castlepoint.gov.uk), serving the Castle Point district, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: castlepoint_gov_uk
      args:
        roadID: ROAD_ID
        street_name: STREET_NAME
```

### Configuration Variables

**roadID**  
*(string) (optional)*

**street_name**  
*(string) (optional)*

Either `roadID` or `street_name` is required.

To find your `roadID`, go to the [Castle Point my street page](https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet&f=homepage1), either enter your street name in the search box or select the first letter of your street, click on the street name, and look for the `roadID` in the URL.

## Example

Using a roadID:

```yaml
waste_collection_schedule:
    sources:
    - name: castlepoint_gov_uk
      args:
        roadID: "4448"
```

Using a street name:

```yaml
waste_collection_schedule:
    sources:
    - name: castlepoint_gov_uk
      args:
        street_name: "Ash Road"
```

# City of Plano ARC Gis

Support for schedules provided by [City of Plano](https://www.plano.gov/), serving City of Plano.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: plano_gov
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
    - name: plano_gov
      args:
        objectID: "1781151"
        daysToGenerate: 3
```

## How to find your `objectID`

- Using a browser, go to [The Plano interactive waste map](https://www.plano.gov/630/Residential-Collection-Schedules).
- Click through the banner and how to use pop up
- Search for your address
- Select your address
- The map should zoom in to your address, **do not click it yet**.
- Open up your browser developer tools
- Click on your house. Your schedule will be displayed.
- In the developer tools, look for an x-protobuf type request.
  
- The URL query params should have something like:

```
f=pbf
objectIds=12345
outFields=ADDRESS%2CBLKY_COLOR%2CBLKY_CURR%2CBLKY_NEXT1%2CBLKY_NEXT2%2CBULKY_DAY%2CDAY_2017%2CHouseNo%2CREC_CURR%2CREC_NEXT1%2CREC_NEXT2%2CREC_WEEK_2017%2CSERVICE%2COBJECTID
outSR=102100
returnGeometry=false
spatialRel=esriSpatialRelIntersects
where=1%3D1
```

- Make note of the `objectIds` value, that will be the arg you need to set in the yaml.

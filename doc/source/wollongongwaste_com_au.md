# Wollongong City Council

Support for schedules provided by [Wollongong Waste](https://www.wollongongwaste.com.au/), serving Wollongong Council in the Illawara, New South Wales, Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wollongongwaste_com_au
      args:
        propertyID: UNIQUE_PROPERTY_ID
```

### Configuration Variables

### Configuration Variables

**propertyID**<br>
*(string) (mandatory)*

This is required. 


#### How to find your `propertyID`

Get your locality.

https://wollongong.waste-info.com.au/api/v1/localities.json
get the locality ID from the above json.

Add it as locality=<id> to the Street query
 eg: https://wollongong.waste-info.com.au/api/v1/streets.json?locality=19
Get the street ID from the above json

Add it as street=<id> to the property query
 eg: https://wollongong.waste-info.com.au/api/v1/properties.json?street=663
get the property ID from the above json.

This is your propertyID

This is all you need to directly query your calendar json in future, you can skip all the above steps once you know your property ID

You could also use [Waste Calendar](https://www.wollongongwaste.com.au/calendar/) with developer tools open on the Network tab, look up your address, and make note of the filename in the last request. It will be in the format <propertyID>.json
 eg: https://wollongong.waste-info.com.au/api/v1/properties/21444.json?start=2022-12-31T13:00:00.000Z&end=2023-12-30T13:00:00.000Z


## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: wollongongwaste_com_au
      args:
        uprn: 21444
```

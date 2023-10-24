# Shellharbour City Council

Support for schedules provided by [Shellharbour City council](https://www.shellharbourwaste.com.au/), serving Shellharbour City Council in the Illawara, New South Wales, Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: shellharbourwaste_com_au
      args:
        zoneID: ZONE_ID
```

### Configuration Variables

**zoneID**  
*(string) (mandatory)*

### How to find your calendarID

Go to <https://www.shellharbourwaste.com.au/find-my-bin-day/>
Put in your address, and click Search.

The site will list the Zone eg: Monday A.

This is the zoneID

Another way is to look for your address in the KML provided by the shellharbourwaste website. 
https://www.shellharbourwaste.com.au/wp-content/uploads/2022/12/Untitled-map-1.kml

This KML has polygons that define the various zones.

## Example

```yaml
waste_collection_schedule:
  sources:
  - name: shellharbourwaste_com_au
    args:
      zoneID: "Monday A"
```

# City of Oklahoma City

Support for schedules provided by [City of Oklahoma City](https://www.okc.gov/), serving City of Oklahoma City.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        try_official: true
        bulkyObjectID: BULKY_WASTE_ZONE_OBJECT_ID
        recycleObjectID: RECYCLE_ZONE_OBJECT_ID
        trashObjectID: TRASH_ZONE_OBJECT_ID
```

### Configuration Variables

**try_official**  
*(boolean) (optional, default=false)*  
When `true`, uses the official OKC Open Data Portal (ArcGIS) services and requires the 3 zone IDs below.

**bulkyObjectID**  
*(string) (required when `try_official=true`)*

**recycleObjectID**  
*(string) (required when `try_official=true`)*

**trashObjectID**  
*(string) (required when `try_official=true`)*

**recycle_reference_date**  
*(string) (optional)*  
A known recycling pickup date (e.g., '2025-06-05') to synchronize every other week schedule. Use if your recycling dates appear to be out of sync.

**objectID**  
*(string) (required when `try_official=false`)*  
Object ID for the unofficial source (`okc.schizo.dev`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        try_official: true
        bulkyObjectID: "14"
        recycleObjectID: "1366"
        trashObjectID: "315"
        recycle_reference_date: "2025-06-05"  # Optional: fix every other week sync
```

## Unofficial example

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        try_official: false
        objectID: "1781151"
```

## How to find official Object IDs

The official source uses ArcGIS FeatureServer endpoints from the OKC Open Data Portal:

- [Trash Zones](https://utility.arcgis.com/usrsvcs/servers/45426e5e1b31489db9afea603870f724/rest/services/OpenData/Utilities/FeatureServer/1)
- [Bulky Waste Zones](https://utility.arcgis.com/usrsvcs/servers/c4455716f4bf4d1dafe6806e0e619de8/rest/services/OpenData/Utilities/FeatureServer/2)
- [Recycle Zones](https://utility.arcgis.com/usrsvcs/servers/0f286e1243ca4bb39a70e323b1608222/rest/services/OpenData/Utilities/FeatureServer/3)

Visit each link above, click "Query" and explore the data to find your zone's OBJECTID based on your address location. Enter these IDs in the corresponding configuration fields.

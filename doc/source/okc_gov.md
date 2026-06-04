# City of Oklahoma City

Support for schedules provided by [City of Oklahoma City](https://www.okc.gov/), serving City of Oklahoma City.

This source uses the official City of Oklahoma City Open Data Portal (ArcGIS FeatureServer) waste collection zone layers.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        trashObjectID: TRASH_ZONE_OBJECT_ID
        recycleObjectID: RECYCLE_ZONE_OBJECT_ID
        bulkyObjectID: BULKY_WASTE_ZONE_OBJECT_ID
```

### Configuration Variables

**trashObjectID**  
*(string|integer) (optional)*  
OBJECTID of your trash collection zone.

**recycleObjectID**  
*(string|integer) (optional)*  
OBJECTID of your recycling zone.

**bulkyObjectID**  
*(string|integer) (optional)*  
OBJECTID of your bulky waste zone.

At least one of the three Object IDs must be provided.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        trashObjectID: 1
        recycleObjectID: 1215
        bulkyObjectID: 1
```

## How to find your Object IDs

The source reads the following ArcGIS FeatureServer layers from the OKC Open Data Portal:

- [Trash Collection Zones](https://utility.arcgis.com/usrsvcs/servers/45426e5e1b31489db9afea603870f724/rest/services/OpenData/Utilities/FeatureServer/1)
- [Recycle Zones](https://utility.arcgis.com/usrsvcs/servers/0f286e1243ca4bb39a70e323b1608222/rest/services/OpenData/Utilities/FeatureServer/3)
- [Bulky Waste Zones](https://utility.arcgis.com/usrsvcs/servers/c4455716f4bf4d1dafe6806e0e619de8/rest/services/OpenData/Utilities/FeatureServer/2)

Open each link above, use the "Query" page to locate the zone polygon that covers your address, and read its `OBJECTID`. Enter those IDs in the corresponding configuration fields.

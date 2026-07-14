# City of Oklahoma City

Support for schedules provided by [City of Oklahoma City](https://www.okc.gov/), serving City of Oklahoma City.

This source supports two methods:

1. **Unofficial community API (`okc.schizo.dev`) — recommended.** A single `recordID` covers trash, recycling and bulky waste, and the API returns explicit upcoming dates.
2. **Official OKC Open Data Portal (ArcGIS FeatureServer).** Requires a separate OBJECTID for each zone (trash, recycling, bulky) and, for recycling, a reference date so the every-other-week cadence can be calculated.

If you configure both, the official source is used first and automatically falls back to the unofficial `recordID` when the official zones return no upcoming collections.

## Configuration via configuration.yaml

### Unofficial source (recommended)

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        recordID: RECORD_ID
```

### Official source

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        trashObjectID: TRASH_ZONE_OBJECT_ID
        recycleObjectID: RECYCLE_ZONE_OBJECT_ID
        bulkyObjectID: BULKY_WASTE_ZONE_OBJECT_ID
        recycle_reference_date: "2026-06-15"
```

### Configuration Variables

**recordID**  
*(string|integer) (optional)*  
Record ID for the unofficial `okc.schizo.dev` source. This single ID covers trash, recycling and bulky waste.

**trashObjectID**  
*(string|integer) (optional)*  
OBJECTID of your trash collection zone (official source).

**recycleObjectID**  
*(string|integer) (optional)*  
OBJECTID of your recycling zone (official source).

**bulkyObjectID**  
*(string|integer) (optional)*  
OBJECTID of your bulky waste zone (official source).

**recycle_reference_date**  
*(string) (optional)*  
ISO date (`YYYY-MM-DD`) of a known recycling collection. OKC recycling runs every other week, but the official portal only exposes a weekday, so provide one real pickup date to pin the correct week. Not needed when using `recordID`.

Provide either `recordID`, or at least one of the three Object IDs.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: okc_gov
      args:
        recordID: 1781503
```

## How to find your `recordID` (recommended)

1. Open [https://okc.schizo.dev/](https://okc.schizo.dev/).
2. Type in your address and select it.
3. Copy the record ID it shows into the `recordID` field.

If your address isn't found, try variations — the underlying OKC database sometimes omits directionals, so `1234 N Sample St` may need to be entered as `1234 Sample St`.

## How to find your Object IDs (official source)

The official method reads the following ArcGIS FeatureServer layers from the OKC Open Data Portal:

- [Trash Collection Zones](https://utility.arcgis.com/usrsvcs/servers/45426e5e1b31489db9afea603870f724/rest/services/OpenData/Utilities/FeatureServer/1)
- [Recycle Zones](https://utility.arcgis.com/usrsvcs/servers/0f286e1243ca4bb39a70e323b1608222/rest/services/OpenData/Utilities/FeatureServer/3)
- [Bulky Waste Zones](https://utility.arcgis.com/usrsvcs/servers/c4455716f4bf4d1dafe6806e0e619de8/rest/services/OpenData/Utilities/FeatureServer/2)

Open each link above, use the "Query" page to locate the zone polygon that covers your address, and read its `OBJECTID`. Enter those IDs in the corresponding configuration fields. Because recycling is every other week and the portal only reports the weekday, also set `recycle_reference_date` to a date you know recycling was collected.

# City of Oklahoma City

Support for schedules provided by [City of Oklahoma City](https://www.okc.gov).

Source for the City of Oklahoma City waste collection schedule. Supports the unofficial okc.schizo.dev API (single recordID) and the official OKC Open Data Portal (ArcGIS) waste collection zones.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: okc_gov
      args:
        recordID: RECORDID
        trashObjectID: TRASHOBJECTID
        recycleObjectID: RECYCLEOBJECTID
        bulkyObjectID: BULKYOBJECTID
        recycle_reference_date: RECYCLE_REFERENCE_DATE
```

### Configuration Variables

**recordID**  
*(string) (optional)*

**trashObjectID**  
*(string) (optional)*

**recycleObjectID**  
*(string) (optional)*

**bulkyObjectID**  
*(string) (optional)*

**recycle_reference_date**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: okc_gov
      args:
        recordID: '1781503'
```

## How to get the source arguments

Recommended: go to https://okc.schizo.dev , type in your address, and copy the record ID it shows into recordID. That single ID covers trash, recycling and bulky waste. If your address isn't found, try variations (e.g. drop a leading 'N'/'North'). Alternatively, use the official OKC data portals to find one OBJECTID per waste type (trashObjectID, recycleObjectID, bulkyObjectID): open the FeatureServer layer for the waste type, zoom into your house, click your zone and read the OBJECTID from the info popup. With the official method, recycling is collected every other week and the portal only reports the weekday, so also set recycle_reference_date to one date you know recycling was (or will be) collected to pin the correct week. If both recordID and official OBJECTIDs are provided, the unofficial recordID source is used first and falls back to the official OBJECTIDs if it fails or returns nothing.

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
When `true`, uses the official `data.okc.gov` datasets and requires the 3 zone IDs below.

**bulkyObjectID**  
*(string) (required when `try_official=true`)*

**recycleObjectID**  
*(string) (required when `try_official=true`)*

**trashObjectID**  
*(string) (required when `try_official=true`)*

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

Using your browser, go to https://data.okc.gov/portal/page/viewer?datasetName=Bulky%20Waste%20Zones&view=map and search for your address.
Go to the table tab and filter by address. Find your Object ID.

Next use the dropdown in the top right hand side of the screen to change the dataset from Bulky Waste Zones to Recycle Zones. Once again Filter by Map to find your Object ID. Do this once more for your Trash Zone.

Once you have these three Object IDs, enter them in `bulkyObjectID`, `recycleObjectID`, and `trashObjectID` and enable `try_official`.

- [trash zones](https://data.okc.gov/portal/page/viewer?datasetName=trash%20zones)
- [bulky waste zones](https://data.okc.gov/portal/page/viewer?datasetName=bulky%20waste%20zones)
- [recycle zones](https://data.okc.gov/portal/page/viewer?datasetName=recycle%20zones)

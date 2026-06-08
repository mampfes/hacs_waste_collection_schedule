# City of Albany

The City of Albany provides waste collection services for residents in Albany, Western Australia. This source uses the council's public ArcGIS FeatureServer layers to determine your collection zone and generate your fortnightly collection schedule.

Collections covered:

- **General Waste & FOGO** (fortnightly, Zone A and Zone B alternate weeks)
- **Recycling** (fortnightly, Zone A and Zone B alternate weeks)

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: albany_wa_gov_au
      args:
        address: "15 Melville Street, Albany WA 6330"
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `address` | Yes | Your street address within the City of Albany (e.g. `15 Melville Street, Albany WA 6330`). Include the suburb and postcode for best results. |

## Finding your collection zone

You can verify your collection zone and day using the City of Albany's interactive map:
<https://albanywa.maps.arcgis.com/apps/webappviewer/index.html?id=ad7f5a181ca04dba8ed7e29ea687152b>

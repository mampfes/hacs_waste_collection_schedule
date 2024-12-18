# City of Los Angeles

Configuration through configuration.yaml:

```yaml
waste_collection_schedule:
  sources:
    - name: lacity_gov
      args:
        street_address: "STREET_ADDRESS"
```

## Configuration Variables

**street_address** *(string) (required)*: Your street address in Los Angeles (e.g., "22472 Denker Ave" or "200 N Spring St")

## Example Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: lacity_gov
      args:
        street_address: "22472 Denker Ave"
```

## How It Works

The integration uses the official LA City GeoQuery API to look up collection schedules. The API returns:

- Collection day of the week for your address
- Services include Black Bin (trash), Blue Bin (recycling), and Green Bin (yard/food waste)
- All bins are collected on the same day of the week.

Collection schedules are provided for a 2-week window from the current date.

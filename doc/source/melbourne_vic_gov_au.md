# City of Melbourne

Support for schedules provided by [City of Melbourne](https://www.melbourne.vic.gov.au/), Victoria, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melbourne_vic_gov_au
      args:
        lat: LATITUDE
        lon: LONGITUDE
```

### Configuration Variables

**lat**
*(float) (required)*

Your latitude, as a decimal number (e.g. `-37.826`).

**lon**
*(float) (required)*

Your longitude, as a decimal number (e.g. `144.946`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: melbourne_vic_gov_au
      args:
        lat: -37.82597212079299
        lon: 144.946122910589
```

## How to get the source arguments

Find your latitude and longitude using [Google Maps](https://www.google.com/maps) or any mapping service. Right-click on your property and select "What's here?" to see the coordinates.

The City of Melbourne has six collection zones, each with weekly general waste and recycling collections on a set day of the week (Monday through Friday). Enter the coordinates of your property and the source will automatically determine which zone you are in.

You can verify your collection zone on the [City of Melbourne garbage collection zones dataset](https://data.melbourne.vic.gov.au/explore/dataset/garbage-collection-zones/).

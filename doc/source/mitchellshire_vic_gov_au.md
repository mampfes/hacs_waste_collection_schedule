# Mitchell Shire Council

Support for schedules provided by [Mitchell Shire Council](https://www.mitchellshire.vic.gov.au), Victoria, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mitchellshire_vic_gov_au
      args:
        lat: LATITUDE
        lon: LONGITUDE
```

### Configuration Variables

**lat**<br>
*(float) (required)*

Your latitude.

**lon**<br>
*(float) (required)*

Your longitude. 

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mitchellshire_vic_gov_au
      args:
        lat: -37.41290975665613
        lon: 144.97998167557827
```

## Obtaining Latitude/Longitude

Find the latitude and longitude of your address using [Google Maps](https://www.google.com/maps) or any other maps service. It should be as accurate as possible (many decimal places) to get the correct schedule.

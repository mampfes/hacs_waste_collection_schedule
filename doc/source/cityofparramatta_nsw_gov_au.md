# City of Parramatta

Support for schedules provided by [City of Parramatta](https://www.cityofparramatta.nsw.gov.au/living-community/waste-recycling/bin-collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cityofparramatta_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cityofparramatta_nsw_gov_au
      args:
        address: "126 Church Street Parramatta"
```

## How to get the source arguments

Enter your full address including the suburb. Example: `126 Church Street Parramatta`.
The integration uses the ArcGIS geocoder to find the coordinates of your address and then queries the City of Parramatta's map service to find your waste collection zone and schedule.

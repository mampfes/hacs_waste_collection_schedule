# Chesapeake, VA

Support for schedules provided by [Chesapeake, VA](https://www.cityofchesapeake.net).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chesapeake_va_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Full street address including city and state.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: chesapeake_va_us
      args:
        address: 460 Sawyers Mill Xing, Chesapeake, VA 23323
```

## How to get the source arguments

Use your full street address including city, state, and ZIP code (e.g. "460 Sawyers Mill Xing, Chesapeake, VA 23323"). The source geocodes the address via the ArcGIS World Geocoder and then queries the city's trash-collection zone layer to determine your weekly pickup day.

Note: Chesapeake has suspended recycling collection city-wide. Only trash collection is currently supported. Recycling support can be added once the city resumes the service.

# Alexandria, VA

Support for schedules provided by [City of Alexandria, VA](https://www.alexandriava.gov/RefuseCollection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: alexandria_va_us
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
    - name: alexandria_va_us
      args:
        address: 301 King St, Alexandria, VA 22314
```

## How to get the source arguments

Use your full street address including city, state, and ZIP code (e.g. "301 King St, Alexandria, VA 22314"). The source geocodes the address via the ArcGIS World Geocoder and then queries the city's refuse and recycle zone layers to determine your weekly trash and recycling pickup days.

Note: Trash is collected for all city residential customers. Recycling is only returned for addresses eligible for city recycling service; addresses without city recycling (e.g. some multi-family or commercial buildings) will only show trash collection. The schedule is a fixed weekly pickup day and does not account for holiday shifts.

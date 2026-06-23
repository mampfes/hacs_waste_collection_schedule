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

Use your full street address including city, state, and ZIP code (e.g. "301 King St, Alexandria, VA 22314"). The source geocodes the address via the ArcGIS World Geocoder and then queries the city's refuse, recycle and leaf zone layers to determine your trash, recycling and seasonal leaf collection dates.

Returned collection types:

- **Trash** — weekly, for all city residential customers.
- **Recycling** — weekly, only for addresses eligible for city recycling service. Addresses without city recycling (e.g. some multi-family or commercial buildings) will not show recycling.
- **Leaf Collection** — seasonal vacuum-leaf collection passes (fall/winter) with explicit dates. The city's data only holds the current season, so leaf entries appear only during the leaf-collection period and are absent the rest of the year.

Note: Trash and recycling are reported as a fixed weekly pickup day and do not account for holiday shifts.

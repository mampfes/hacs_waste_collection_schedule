# Prince George's County, MD

Support for schedules provided by [Prince George's County, MD](https://www.princegeorgescountymd.gov/departments-offices/environment/waste-recycling/residential-collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: prince_georges_county_md_us
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
    - name: prince_georges_county_md_us
      args:
        address: 6807 McCormick Rd, Upper Marlboro, MD
```

## How to get the source arguments

Use your full street address including city and state (e.g. "6807 McCormick Rd, Upper Marlboro, MD"). The source geocodes the address via the ArcGIS World Geocoder and then queries the County's residential collection lookup layer — the same data that backs the County's own [online address tool](http://princegeorges.maps.arcgis.com/apps/webappviewer/index.html?id=7e1968cf75524789a2fd131afe6ea6b4) — to determine your collection days.

Returned collection types:

- **Trash** — weekly, for all County-collected residential customers.
- **Recycling** — weekly, for addresses eligible for County recycling service.
- **Bulky Trash** — weekly, on the same day as regular trash (up to 4 items, no appointment needed).
- **Yard Trim** — weekly, always on Monday, year-round.

Addresses that are not enrolled in County-collected waste service (e.g. commercial properties or addresses using a private hauler) will raise an error, since there is no County collection schedule to report.

Note: Collection days are reported as a fixed weekly pickup day and do not account for holiday shifts. Curbside electronics/scrap-metal and appliance/white-goods pickups are by appointment only and are not covered by this source.

# Shoalhaven City Council

Support for schedules provided by [Shoalhaven City Council](https://www.shoalhaven.nsw.gov.au/).

Source script for shoalhaven.nsw.gov.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: shoalhaven_nsw_gov_au
      args:
        street_address: STREET_ADDRESS
        geolocation_id: GEOLOCATION_ID
```

### Configuration Variables

**street_address**  
*(string) (optional)*

**geolocation_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: shoalhaven_nsw_gov_au
      args:
        street_address: 2 Cherry Plum Way, WORRIGEE
```

## How to get the source arguments

Enter your street address as the council's own address search shows it, e.g. "2 Cherry Plum Way, WORRIGEE". You can check it on the <https://www.shoalhaven.nsw.gov.au/My-Area> page. Alternatively give the Location ID, the council's geolocation ID. It skips the address lookup and takes precedence when both are given. To find it, open your browser's developer tools (F12, Network tab), select your address on the page above and look for the request `https://www.shoalhaven.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<ID>&ocsvclang=en-AU`. The value after `geolocationid=` is your Location ID.

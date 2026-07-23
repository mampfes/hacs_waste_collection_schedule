# Surf Coast Shire, VIC

Support for schedules provided by [Surf Coast Shire Bin collection calendars](https://www.surfcoast.vic.gov.au/Property/Waste-and-recycling/Kerbside-bins/Bin-collection-calendars), the same lookup used by the official SCRRApp ([Apple](https://apps.apple.com/au/app/scrrapp/id1547443364) / [Google Play](https://play.google.com/store/apps/details?id=com.socketsoftware.whatbinday.surfcoast)).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: surf_coast_vic_gov_au
      args:
        street_number: STREET_NUMBER
        street_name: STREET_NAME
        suburb: SUBURB
        post_code: POST_CODE
```

### Configuration Variables

**street_number**  
*(string) (required)*

**street_name**  
*(string) (required)*

**suburb**  
*(string) (required)*

Must be entered in Title Case (e.g. `Torquay`), not upper case (`TORQUAY`) — the upstream lookup matches suburb names case-sensitively.

**post_code**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: surf_coast_vic_gov_au
      args:
        street_number: "20"
        street_name: "Bell Street"
        suburb: "Torquay"
        post_code: "3228"
```

## How to get the source arguments

1. Visit the [Bin collection calendars](https://www.surfcoast.vic.gov.au/Property/Waste-and-recycling/Kerbside-bins/Bin-collection-calendars) page and search for your address to confirm it is serviced.
2. Enter the street number, street name, suburb and postcode of your address. The suburb must be in Title Case (e.g. `Lorne`, `Anglesea`, `Torquay`) exactly as it appears on the council's own address list.

## Notes

This source geocodes the supplied address via [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) and then queries the same public WhatBinDay API used by the SCRRApp mobile app. A very small number of addresses may not resolve to a coordinate precise enough for the upstream lookup to match a serviced address (this appears to affect a handful of properties even in the mobile app itself), in which case the source will raise an error asking you to check the address.

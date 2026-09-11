# Shoalhaven City Council

Support for schedules provided by [Shoalhaven City Council](https://www.shoalhaven.nsw.gov.au/), NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: shoalhaven_nsw_gov_au
      args:
        street_address: STREET_ADDRESS
```

## Configuration Variables

**street_address**  
*(string) (optional)* Your street address, as the council's own address search shows it.

**geolocation_id**  
*(string) (optional)* The council's internal ID for your property. Only needed if the address search cannot find it; used in preference to `street_address` when both are given.

One of `street_address` or `geolocation_id` is required.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: shoalhaven_nsw_gov_au
      args:
        street_address: "2 Cherry Plum Way, WORRIGEE"
```

```yaml
waste_collection_schedule:
    sources:
    - name: shoalhaven_nsw_gov_au
      args:
        geolocation_id: "2ea7b0c7-b627-421d-8436-248b8da384b6"
```

## How to get the source argument

Enter your address on the [My Area](https://www.shoalhaven.nsw.gov.au/My-Area) page and use it as the address search shows it, e.g. `2 Cherry Plum Way, WORRIGEE`.

To find a Geolocation ID instead:

1. Go to the Shoalhaven City Council [My Area](https://www.shoalhaven.nsw.gov.au/My-Area) page.
2. Open Developer Tools in your browser by pressing F12 and go to the Network tab.
3. Enter your address in the search bar and select it from the suggestions.
4. Once your address information is displayed, look at the `wasteservices` URL in the Network tab.
5. Copy the long string of letters and numbers that follows `geolocationid=` (e.g. `2ea7b0c7-b627-421d-8436-248b8da384b6`). This is your Geolocation ID.

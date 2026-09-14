# Wagga Wagga City Council

Support for schedules provided by [Wagga Wagga City Council - What Is My Bin Day?](https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: YOUR_FULL_ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Your full property address, formatted as you'd type it into the council's own "What Is My Bin Day?" search, e.g. `15 Fitzhardinge Street, Wagga Wagga NSW`. This is geocoded automatically (via OpenStreetMap Nominatim) and converted to the MGA Zone 55 coordinates the council's own tool actually uses for the lookup.

Nominatim works well for many addresses, but doesn't have house-number-level data for every street in the Wagga area -- when that's the case, geocoding can land on the wrong property (or fail) even though the street itself is found. If that happens for your address, use `x`/`y` instead (see below), which is also the more reliable option in general.

**x** *(float) (optional)*

**y** *(float) (optional)*

MGA Zone 55 (GDA94, EPSG:28355) easting/northing. Supply both to skip geocoding entirely. Get the values once from the council's own tool by inspecting the URL it navigates to after a search (it will contain `x=...&y=...`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: 15 Fitzhardinge Street, Wagga Wagga NSW
```

Or, with explicit coordinates instead of an address lookup (recommended if geocoding doesn't find your exact property):

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: 24 Docker Street, Wagga Wagga NSW
        x: 532385.29
        y: 6113636.31
```

## How to get the source arguments

1. Visit the [Wagga Wagga City Council "What Is My Bin Day?" page](https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day).
2. Search for your property address and confirm the council's tool returns a schedule for it.
3. Try that same address (suburb + "NSW" is usually enough) as the `address` argument first.
4. If it doesn't resolve correctly (wrong property, or an error), look at the URL the council's page navigated to after your search -- it will contain `x=...&y=...` -- and pass those two values as the `x`/`y` arguments instead.

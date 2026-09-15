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

Your full property address, formatted as you'd type it into the council's own "What Is My Bin Day?" search, e.g. `24 Docker Street, Wagga Wagga NSW`. This is shown back on the council's results and is geocoded automatically (via Esri's World Geocoding Service) to house-level precision if `x`/`y` are not supplied.

**x** *(float) (optional)*

**y** *(float) (optional)*

MGA Zone 55 (GDA94, EPSG:28355) easting/northing for your property, for the rare case where automatic geocoding doesn't resolve your exact address. Get the values from the council's own tool by inspecting the URL it navigates to after a search (it will contain `x=...&y=...`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: 24 Docker Street, Wagga Wagga NSW
```

## How to get the source arguments

Just your full property address, e.g. `24 Docker Street, Wagga Wagga NSW` -- it is geocoded automatically.

If your address doesn't resolve correctly, you can instead supply the exact `x`/`y` coordinates:

1. Visit the [Wagga Wagga City Council "What Is My Bin Day?" page](https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day).
2. Search for your property address and confirm the council's tool returns a schedule for it.
3. Look at the URL the page navigated to after your search -- it will contain `x=...&y=...` -- and use those two values as the `x`/`y` arguments, along with the address you searched for as the `address` argument.

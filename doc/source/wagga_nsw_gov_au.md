# Wagga Wagga City Council

Support for schedules provided by [Wagga Wagga City Council - What Is My Bin Day?](https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: YOUR_FULL_ADDRESS
        x: YOUR_X_COORDINATE
        y: YOUR_Y_COORDINATE
```

### Configuration Variables

**address**
*(string) (required)*

Your full property address, formatted as you'd type it into the council's own "What Is My Bin Day?" search, e.g. `24 Docker Street, Wagga Wagga NSW`. This is shown back on the council's results and is used as a geocoding fallback (via OpenStreetMap Nominatim) if `x`/`y` are not supplied.

**x** *(float) (optional, but strongly recommended)*

**y** *(float) (optional, but strongly recommended)*

MGA Zone 55 (GDA94, EPSG:28355) easting/northing for your property. Get the values once from the council's own tool by inspecting the URL it navigates to after a search (it will contain `x=...&y=...`).

Supplying `x`/`y` is effectively required for a complete result. OpenStreetMap Nominatim (the free geocoder used when `x`/`y` are omitted) only has street-centreline data for Wagga, not house-level data. That's precise enough to find the area-wide green waste roster, but not precise enough for the property-specific domestic waste/recycling roster, which needs a point accurate to your actual block. An address-only lookup will reliably raise an error telling you it couldn't find your domestic waste/recycling schedule -- this isn't a bug, it's a limitation of the free geocoding data available for this council area, and supplying `x`/`y` avoids it entirely.

## Example

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
3. Look at the URL the page navigated to after your search -- it will contain `x=...&y=...` -- and use those two values as the `x`/`y` arguments, along with the address you searched for as the `address` argument.

# Wagga Wagga City Council

Support for schedules provided by [Wagga Wagga City Council](https://wagga.nsw.gov.au).

Source for Wagga Wagga City Council, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: ADDRESS
        x: X
        y: Y
```

### Configuration Variables

**address**  
*(string) (required)*

**x**  
*(string) (optional)*

**y**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wagga_nsw_gov_au
      args:
        address: 24 Docker Street, Wagga Wagga NSW
```

## How to get the source arguments

Enter your full property address (e.g. '24 Docker Street, Wagga Wagga NSW'). This is geocoded automatically. If your address doesn't resolve correctly, you can instead supply the exact 'x' and 'y' MGA Zone 55 (GDA94, EPSG:28355) coordinates from the council's own 'What Is My Bin Day?' tool: search your address there and read them out of the URL it navigates to (it will contain 'x=...&y=...').

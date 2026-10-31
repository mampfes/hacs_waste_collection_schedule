# Christchurch City Council

Support for schedules provided by [Christchurch City Council](https://ccc.govt.nz).

Source for Christchurch City Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ccc_govt_nz
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ccc_govt_nz
      args:
        address: 53 Hereford Street
```

## How to get the source arguments

Enter your street address as the council's bin-day lookup on https://ccc.govt.nz finds it, e.g. 53 Hereford Street. Only the dates the council currently plans are shown; a round the council has no current date for is left out. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.

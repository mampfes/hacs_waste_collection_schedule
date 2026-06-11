# Mid-Western Regional Council

Support for schedules provided by [Mid-Western Regional Council](https://www.midwestern.nsw.gov.au/), serving the Mid-Western region (Mudgee, Gulgong, Kandos, Rylstone) in New South Wales, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midwestern_nsw_gov_au
      args:
        area: AREA
```

### Configuration Variables

**area**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: midwestern_nsw_gov_au
      args:
        area: mudgee_north_monday
```

## How to get the source arguments

Pick the entry for your suburb and regular collection day. Valid values:

- `mudgee_north_monday`
- `mudgee_north_thursday`
- `mudgee_south_tuesday`
- `mudgee_south_wednesday`
- `gulgong_monday`
- `gulgong_thursday`
- `kandos_rylstone_friday`

If you are not sure which area applies to you, check the [Mid-Western Regional Council bin collection calendar](https://www.midwestern.nsw.gov.au/Services/Waste-and-recycling).

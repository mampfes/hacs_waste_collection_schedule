# Isaac Regional Council

Support for schedules provided by [Isaac Regional Council](https://www.isaac.qld.gov.au/residents/waste/kerbside-collection).

Source for Isaac Regional Council, Queensland, Australia (general waste, weekly).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: isaac_qld_gov_au
      args:
        town: TOWN
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**town**  
*(string) (required)*

**collection_day**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: isaac_qld_gov_au
      args:
        town: Glenden
```

## How to get the source arguments

Select your town. The smaller towns (Coastal, Glenden, Middlemount, Nebo) have a single town-wide collection day, read automatically. The larger towns (Clermont, Dysart, Moranbah) have several days that depend on your street: look your day up on the council's collection map and select it in 'Collection day'. Only the weekly general waste (red lid) collection is provided; the fortnightly recycling phase is map-only and not available as a live feed.

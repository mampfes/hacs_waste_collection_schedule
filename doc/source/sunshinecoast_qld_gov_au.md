# Sunshine Coast Queensland (QLD)

Support for schedules provided by [Sunshine Coast Queensland (QLD)](https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days).

Source script for Sunshine Coast Queensland (QLD).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: STREET_NAME
        locality: LOCALITY
```

### Configuration Variables

**street_name**  
*(string) (required)*

**locality**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: hospital rd
```

## How to get the source arguments

Enter the street name as shown by the council's bin checker. House numbers, a comma-separated suburb and spelled-out street types are accepted. Use locality when a street occurs in several suburbs. The current published widget supplies the week-cycle anchor; the API supplies your street's weekday and week. Collections happening today are included. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

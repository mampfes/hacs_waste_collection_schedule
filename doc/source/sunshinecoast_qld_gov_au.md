# Sunshine Coast Queensland

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: "Hospital Rd"
        locality: "Nambour"
```

Use the [council bin checker](https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days) to find your street.

- `street_name`: Street name. House numbers, a comma-separated suburb and spelled-out street types are accepted.
- `locality` (optional): Suburb, required when the street name has multiple matches.

The street API supplies the collection weekday and week 1/2 assignment. The source reads the cycle anchor from the currently published bin widget and returns ten dates per collection type. Collections happening today are included, matching the council widget. The garden bin is mapped to canonical garden waste.

## BaseSource migration

Configuration argument names stay unchanged. Waste types now use canonical, localised names; update filters, automations and customisations using the former labels.

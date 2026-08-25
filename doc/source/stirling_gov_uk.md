# Stirling Council

Support for schedules provided by [Stirling Council](https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/), serving Stirlingshire, UK.

Stirling Council publishes its collection calendar via Routeware's ReCollect platform. This source looks up your address through the same API used by the council's bin collection dates search, so you only need to provide your address as you would type it there — no need to extract a calendar URL manually.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_gov_uk
      args:
        address: "38 Kildean Road"
```

### Configuration Variables

**address**
*(string) (required)*

Your address as entered on the [Stirling Council bin collection dates search](https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/). All of the following resolve to a single property:

- house number and street: `38 Kildean Road`
- property name: `Merlo`
- a single-dwelling postcode: `FK8 1TB`

For multi-dwelling postcodes the search returns a postcode rather than a property — add your house number or property name to make it unique.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_gov_uk
      args:
        address: "38 Kildean Road"
```

returns collections for `38 Kildean Road, Kildean, Stirling, FK8 1TB` with the waste types `Non-recyclable Waste`, `Food and Garden`, `Paper & Cardboard`, `Plastic, cans and cartons` and `Glass`.

## Suggested Lovelace card setup

The integration populates the built-in Home Assistant calendar with one event per waste type. If you use [TrashCard](https://github.com/idaho/hassio-trash-card), the following patterns match the waste type names exactly (`pattern_exact: true`, to avoid e.g. `recycle` matching `Non-recyclable`) and colour the chips like the corresponding Stirling bin lids (grey, brown, green, blue, purple):

```yaml
 type: custom:trash-card
 entities:
   - calendar.stirling_council
 event_grouping: true
 next_days: 6
 with_label: true
 pattern:
   - type: waste
     pattern: "Non-recyclable Waste"
     pattern_exact: true
     icon: mdi:trash-can
     color: grey
     label: General waste
   - type: organic
     pattern: "Food and Garden"
     pattern_exact: true
     icon: mdi:leaf
     color: brown
     label: Food & garden
   - type: paper
     pattern: "Paper & Cardboard"
     pattern_exact: true
     icon: mdi:package-variant
     color: green
     label: Paper & card
   - type: recycle
     pattern: "Plastic, cans and cartons"
     pattern_exact: true
     icon: mdi:recycle-variant
     color: blue
     label: Cans & plastics
   - type: custom
     pattern: "Glass"
     pattern_exact: true
     icon: mdi:bottle-soda
     color: purple
     label: Glass
```

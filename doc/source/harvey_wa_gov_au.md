# Shire of Harvey

Support for schedules provided by [Shire of Harvey](https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/bin-collection-residential-and-commercial).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: harvey_wa_gov_au
      args:
        suburb: SUBURB
        recycling_in_even_week: true
```

### Configuration Variables

**suburb**
*(string) (required)*

Your suburb or collection area as listed on the Shire of Harvey bin collection page, e.g. Yarloop or Australind (south of Paris Road).

**recycling_in_even_week**
*(boolean) (optional, default: True)*

Set to True if your recycling bin is collected on even ISO week numbers, False if collected on odd ISO week numbers. Check your last recycling collection date to determine this (use a site like [whatweekisit.org](https://whatweekisit.org/)).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: harvey_wa_gov_au
      args:
        suburb: Roelands including Raymond Road
        recycling_in_even_week: true
```

## How to get the source arguments

1. Visit the [Shire of Harvey bin collection page](https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/bin-collection-residential-and-commercial).
2. Expand the accordion for your collection day and find your suburb or area in the list. Use the exact text shown.
3. To determine recycling_in_even_week: note the date of your last recycling collection, look up its ISO week number (e.g. using [whatweekisit.org](https://whatweekisit.org/)), and set the value to True if even, False if odd.

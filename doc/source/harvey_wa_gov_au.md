# Shire of Harvey

Support for schedules provided by [Shire of Harvey](https://www.harvey.wa.gov.au).

Source for Shire of Harvey (WA) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: harvey_wa_gov_au
      args:
        suburb: SUBURB
        recycling_in_even_week: RECYCLING_IN_EVEN_WEEK
```

### Configuration Variables

**suburb**  
*(string) (required)*

**recycling_in_even_week**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: harvey_wa_gov_au
      args:
        suburb: Australind (south of Paris Road)
        recycling_in_even_week: true
```

## How to get the source arguments

Visit https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/bin-collection-residential-and-commercial and find your suburb in the collection day list. Use the exact text shown, e.g. 'Yarloop' or 'Australind (south of Paris Road)'. For recycling_in_even_week: check your last recycling collection date and see if its ISO week number (https://whatweekisit.org/) was even (True) or odd (False).

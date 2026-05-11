# Shire of Dardanup

Support for schedules provided by [Shire of Dardanup](https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/find-your-bin-day.aspx).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        street: STREET_NAME
        recycling_in_even_week: true
```

### Configuration Variables

**street**
*(string) (optional)*

Your street name without a house number, e.g. `Hale Street` or `Flinders Street`. Used to automatically look up your collection day from the Shire website. Provide either `street` or `collection_day`.

**collection_day**
*(string) (optional)*

Your collection day as a string: `Monday`, `Tuesday`, `Wednesday`, `Thursday`, or `Friday`. Use this instead of `street` for Dardanup West (Monday) and Ferguson Valley residents, or if street lookup fails.

**recycling_in_even_week**
*(boolean) (optional, default: `true`)*

Set to `true` if your recycling bin is collected on even ISO week numbers, `false` if on odd ISO week numbers. Check your last recycling collection date to determine this (use [whatweekisit.org](https://whatweekisit.org/)).

## Example — street lookup

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        street: Hale Street
        recycling_in_even_week: true
```

## Example — direct day (Dardanup West / Ferguson Valley)

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        collection_day: Monday
        recycling_in_even_week: false
```

## How to get the source arguments

1. Visit the [Shire of Dardanup Find Your Bin Day page](https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/find-your-bin-day.aspx).
2. Find your street in the accordion lists for Area 1 or Area 2, or note your collection day directly (Area 3 = Monday; Ferguson Valley residents should check the Waste Guide PDF linked on that page).
3. Enter your street name (without house number) as `street`, or enter the day as `collection_day`.
4. To determine `recycling_in_even_week`: note the date of your last recycling collection, look up its ISO week number (e.g. using [whatweekisit.org](https://whatweekisit.org/)), and set `true` if even, `false` if odd.

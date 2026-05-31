# Fairfield City Council

Support for schedules provided by [Fairfield City Council](https://kerbside.fairfieldcity.nsw.gov.au/kerbside/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fairfieldcity_nsw_gov_au
      args:
        street_number: YOUR_STREET_NUMBER
        street_and_suburb: YOUR_STREET_AND_SUBURB
```

### Configuration Variables

**street_number**
*(string) (required)*

Your street number (e.g. `1`, `7A`, `7/10`).

**street_and_suburb**
*(string) (required)*

Your street name and suburb exactly as it appears in the autocomplete list on the council's kerbside lookup page (e.g. `Dawson ST, FAIRFIELD HEIGHTS`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fairfieldcity_nsw_gov_au
      args:
        street_number: "1"
        street_and_suburb: "Dawson ST, FAIRFIELD HEIGHTS"
```

## How to get the source arguments

1. Visit the [Fairfield City Council kerbside lookup](https://kerbside.fairfieldcity.nsw.gov.au/kerbside/).
2. Start typing your street name into the **Street name & Suburb** field and select your street from the autocomplete list.
3. Use the selected autocomplete value (e.g. `Dawson ST, FAIRFIELD HEIGHTS`) as `street_and_suburb`.
4. Enter your house or unit number as `street_number`.

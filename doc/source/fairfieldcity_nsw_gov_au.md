# Fairfield City Council

Support for schedules provided by [Fairfield City Council](https://kerbside.fairfieldcity.nsw.gov.au/kerbside/).

Source for Fairfield City Council bin collection, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fairfieldcity_nsw_gov_au
      args:
        street_number: STREET_NUMBER
        street_and_suburb: STREET_AND_SUBURB
```

### Configuration Variables

**street_number**  
*(string) (required)*

**street_and_suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fairfieldcity_nsw_gov_au
      args:
        street_number: '1'
        street_and_suburb: Dawson Street, FAIRFIELD HEIGHTS
```

## How to get the source arguments

Visit https://kerbside.fairfieldcity.nsw.gov.au/kerbside/ and start typing your street name and suburb into the 'Street name & Suburb' field. Use the autocomplete suggestion (e.g. 'Dawson Street, FAIRFIELD HEIGHTS') as the street, including the suburb, and enter just your street number (e.g. 1, 7A, 7/10) as the house number. Abbreviated street types from older configurations (e.g. 'Dawson ST, FAIRFIELD HEIGHTS') are still accepted. The council shows the next collection of each bin. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.

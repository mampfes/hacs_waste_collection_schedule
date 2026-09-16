# Surf Coast Shire

Support for schedules provided by [Surf Coast Shire](https://www.surfcoast.vic.gov.au).

Source for Surf Coast Shire (VIC) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: surf_coast_vic_gov_au
      args:
        street_name: STREET_NAME
        street_number: STREET_NUMBER
        post_code: POST_CODE
        suburb: SUBURB
```

### Configuration Variables

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

**post_code**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: surf_coast_vic_gov_au
      args:
        street_number: '20'
        street_name: Bell Street
        suburb: Torquay
        post_code: '3228'
```

## How to get the source arguments

Visit the Surf Coast Shire 'Bin collection calendars' page (https://www.surfcoast.vic.gov.au/Property/Waste-and-recycling/Kerbside-bins/Bin-collection-calendars), search for your address, then enter the street number, street name, suburb and postcode as they appear there.

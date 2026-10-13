# Shire of Mundaring

Support for schedules provided by [Shire of Mundaring](https://www.mundaring.wa.gov.au/).

Source for mundaring.wa.gov.au services for the Shire of Mundaring, Western Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mundaring_wa_gov_au
      args:
        parcel_number: PARCEL_NUMBER
        suburb: SUBURB
```

### Configuration Variables

**parcel_number**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mundaring_wa_gov_au
      args:
        parcel_number: 103239
        suburb: Helena Valley
```

## How to get the source arguments

An easy way to discover your parcel_number is by going to https://geohub-mundaring.hub.arcgis.com/, and use the Property Map to search for your address ensuring both Lot Numbers and House Number checkboxes are ticked. The pop-up that appears contains an entry that shows your parcel number.

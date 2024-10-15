# Shire of Mundaring

Support for schedules provided by the [Shire of Mundaring](https://mundaring.wa.gov.au/), in Western Australia.

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
*(integer | string)*

The unique reference number that identified your property

**suburb**  
*(string)*

The suburb for your address

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: mundaring_wa_gov_au
      args:
        parcel_number: 103239
        suburb: "Helena Valley"
```

## How to get the parcel_number source argument

An easy way to discover your parcel_number is by going to https://geohub-mundaring.hub.arcgis.com/, and use the *Property Map* to search for your address ensuring both *Lot Numbers* and *House Number* checkboxes are ticked. The pop-up that appears contains an entry that shows your parcel number.
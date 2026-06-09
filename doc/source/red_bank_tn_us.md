# Red Bank, Tennessee

Support for schedules provided by the [City of Red Bank, TN](https://www.redbanktn.gov/257/Solid-Waste) via their public ArcGIS services.

The city splits residential trash collection into five weekday zones (Monday–Friday). This source resolves your collection weekday from your street address, projects the weekly schedule one year ahead, and applies the city's holiday delays (federal holidays, Good Friday and the day after Thanksgiving shift collection to the next non-holiday weekday).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: red_bank_tn_us
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address** _(string) (required)_: Street address of the property within the City of Red Bank, TN.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: red_bank_tn_us
      args:
        street_address: "1107 Ashmore Ave"
```

## How to find your street address

Use your street address as it appears on city records. The city/state/ZIP are optional — only the house number and street name are used to look up your parcel.

You can verify your address and collection weekday on the city's official [trash-day map](https://www.redbanktn.gov/257/Solid-Waste) ("New Trash Service").

Examples of valid formats:
- "1107 Ashmore Ave"
- "20 Mason Dr, Red Bank, TN 37415"

Common street-type suffixes (St, Ave, Rd, Dr, Ln, Blvd, …) and unit designators (Apt, Unit, …) are ignored when matching, so minor variations in formatting should still work.

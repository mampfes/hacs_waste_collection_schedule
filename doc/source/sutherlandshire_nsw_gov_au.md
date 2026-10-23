# Sutherland Shire Council

Support for schedules provided by [Sutherland Shire Council](https://www.sutherlandshire.nsw.gov.au).

Source for Sutherland Shire Council, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sutherlandshire_nsw_gov_au
      args:
        suburb: SUBURB
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sutherlandshire_nsw_gov_au
      args:
        suburb: BONNET BAY
        street: Cleveland Place
        house_number: '5'
```

## How to get the source arguments

Use the address exactly as it appears on council correspondence, with the street type spelled out in full (Street, Place, Avenue). You can check your address on the map at https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection

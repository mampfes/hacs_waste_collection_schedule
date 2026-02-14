# Hornsby Shire Council

Support for schedules provided by [Hornsby Shire Council](https://www.hornsby.nsw.gov.au/Property/Waste-and-recycling/Your-weekly-collection/Find-your-waste-collection-dates).

The source extracts collection dates directly from the PDF calendars published by the council, including:
- **Green Waste** (green lid bin)
- **Recycling** (yellow lid bin)
- **General Waste** (red lid bin) - collected on both green and recycling weeks
- **Bulky Waste** - if available for your property

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hornsby_nsw_gov_au
      args:
        address: STREET_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Your street address within Hornsby Shire, exactly as it appears when searching on the [council's waste collection page](https://www.hornsby.nsw.gov.au/Property/Waste-and-recycling/Your-weekly-collection/Find-your-waste-collection-dates).

**Note:** Include the street number, street name, suburb, and postcode, but do not include the state (NSW) or country. For example: `1 Cherrybrook Road, West Pennant Hills, 2125`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hornsby_nsw_gov_au
      args:
        address: "1 Cherrybrook Road, West Pennant Hills, 2125"
```

## How to get the source arguments

1. Visit the [Hornsby Shire Council waste collection page](https://www.hornsby.nsw.gov.au/Property/Waste-and-recycling/Your-weekly-collection/Find-your-waste-collection-dates).
2. Enter your address in the search box and select your property from the autocomplete suggestions.
3. Use the exact address text that was autocompleted/selected (including the suburb but without state or postcode).
4. Copy this address into your Home Assistant configuration.

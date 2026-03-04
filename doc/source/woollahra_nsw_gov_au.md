# Woollahra Municipal Council (NSW)

Support for schedule provided by [Woollahra Municipal Council](https://www.woollahra.nsw.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: woollahra_nsw_gov_au
      args:
        address: "YOUR_FULL_ADDRESS"
```

### Configuration Variables

**address**  
*(string) (required)*

Your full address exactly as it appears on the Woollahra Municipal Council website. Include street number, street name, suburb, state (NSW), and postcode. If you have issues, copy and paste it once the search has completed, at this url: https://www.woollahra.nsw.gov.au/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: woollahra_nsw_gov_au
      args:
        address: "22 Dudley Street PADDINGTON NSW 2021"
```

## How to find your address

1. Go to [Woollahra Municipal Council website](https://www.woollahra.nsw.gov.au/)
2. Navigate to Services -> Rubbish and Recycling -> Find your rubbish and scheduled clean-up service dates
3. Enter your address in the search box and note the exact format that appears in the search results
4. Copy and paste this exact address format into your configuration

**Important:** Use the exact address format as shown on the council website, including correct capitalization and spacing.

The source will return collection schedules for:

- General Waste (red lid bin)
- Green Waste (green lid bin for organics)
- Recycling (yellow lid bin)
- Seasonal scheduled clean-ups (Spring, Summer, Winter)

## Notes

This source uses the Woollahra Municipal Council's API and includes retry logic to handle potential bot protection measures. If you encounter access issues, please try again later as the website may temporarily block automated requests.

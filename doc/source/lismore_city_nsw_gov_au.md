# Lismore City Council

Support for schedules provided by [Lismore City Council](https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lismore_city_nsw_gov_au
      args:
        address: YOUR_FULL_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Your full street address exactly as it appears in the Lismore City Council bin-day search.

This source is intended for addresses serviced by Lismore City Council, including localities such as Lismore, Goonellabah, East Lismore, Lismore Heights, Nimbin, Clunes, Dunoon, The Channon, and nearby areas within the council area.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lismore_city_nsw_gov_au
      args:
        address: "1 Rosella Chase, Goonellabah NSW 2480"
```

## How to get the source arguments

1. Visit the [Lismore City Council bin-day page](https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1).
2. Search for your property address.
3. Use the full address exactly as shown in the search result.

Example towns/localities were taken from the [City of Lismore Wikipedia page](https://en.wikipedia.org/wiki/City_of_Lismore) as documentation aids only. Actual service coverage is determined by the council lookup.

## Notes

This source uses Lismore's public WhatBinDay-backed bin-day service. Use the full address shown by the website.

## Optional local bin images

If you prefer to host the bin images locally in Home Assistant instead of using the remote image URLs, download these files and place them in `<config>/www/waste`:

- `wheelie-recycle-yellow.png`
- `wheelie-green-limegreen.png`
- `wheelie-waste-red.png`

Source URLs:

- `https://whatbinday.com/api/images/wheelie-recycle-yellow.png`
- `https://whatbinday.com/api/images/wheelie-green-limegreen.png`
- `https://whatbinday.com/api/images/wheelie-waste-red.png`

Steps:

1. Open each image URL in your browser.
2. Save each file using the same filename.
3. Copy the files to:

```text
<config>/www/waste
```

They will then be available in Home Assistant as:

- `/local/waste/wheelie-recycle-yellow.png`
- `/local/waste/wheelie-green-limegreen.png`
- `/local/waste/wheelie-waste-red.png`

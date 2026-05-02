# Ballina Shire Council

Support for schedules provided by [Ballina Shire Council](https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ballina_nsw_gov_au
      args:
        address: YOUR_FULL_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Your full street address exactly as it appears in the Ballina Shire Council bin-day search.

This source is intended for addresses serviced by Ballina Shire Council, including localities such as Ballina, Alstonville, Lennox Head, Tintenbar, Wardell, Wollongbar, and nearby areas within the shire.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ballina_nsw_gov_au
      args:
        address: "1 Grant St, Ballina NSW 2478"
```

## How to get the source arguments

1. Visit the [Ballina Shire Council bin-day page](https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day).
2. Search for your property address.
3. Use the full address exactly as shown in the search result.

Example towns/localities were taken from the [Ballina Shire Wikipedia page](https://en.wikipedia.org/wiki/Ballina_Shire) as documentation aids only. Actual service coverage is determined by the council lookup.

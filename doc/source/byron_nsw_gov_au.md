# Byron Shire Council

Support for schedules provided by [Byron Shire Council](https://www.byron.nsw.gov.au/Residential-Services/Waste-Recycling/Bin-Collection-Services/Bin-Collection-Schedules).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: byron_nsw_gov_au
      args:
        address: YOUR_FULL_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Your full street address exactly as it appears in the Byron Shire Council bin collection lookup.

This source is intended for addresses serviced by Byron Shire Council, including localities such as Byron Bay, Bangalow, Suffolk Park, Brunswick Heads, Mullumbimby, Ocean Shores, Federal, Main Arm, and nearby areas within the shire.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: byron_nsw_gov_au
      args:
        address: "120 Jonson St, Byron Bay"
```

## How to get the source arguments

1. Visit the [Byron Shire Council bin collection schedules page](https://www.byron.nsw.gov.au/Residential-Services/Waste-Recycling/Bin-Collection-Services/Bin-Collection-Schedules).
2. Search for your property address.
3. Use the full address exactly as shown in the search result.

Example towns/localities were taken from the [Byron Shire Wikipedia page](https://en.wikipedia.org/wiki/Byron_Shire) as documentation aids only. Actual service coverage is determined by the council lookup.

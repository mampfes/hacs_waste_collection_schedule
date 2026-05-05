# Kempsey Shire Council

Support for schedules provided by [Kempsey Shire Council](https://www.kempsey.nsw.gov.au), New South Wales, Australia.

## Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
  sources:
    - name: kempsey_nsw_gov_au
      args:
        address: FULL_STREET_ADDRESS
```

## Configuration Variables

**address** *(string)* *(required)*: Your full street address including suburb, exactly as it appears on the Kempsey Shire Council website.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kempsey_nsw_gov_au
      args:
        address: "10-12 Smith Street Kempsey"
```

> **Note:** If your address lookup returns no results, try variations of your address as it appears on council correspondence, e.g. including or excluding the suburb name.

## Collection Schedule

The following bins are collected on a weekly or fortnightly basis:

| Bin | Collection Frequency |
|-----|----------------------|
| Green Organics Bin | Weekly |
| Red Rubbish Bin | Fortnightly |
| Yellow Recycling Bin | Fortnightly (alternating with Red Rubbish Bin) |

## Christmas / New Year Period

During the Christmas and New Year period (approximately **22 December to 2 January**), Kempsey Shire Council alters the bin collection schedule. Typically all three bins are collected both weeks during this period.

Collection dates falling within this window will show a warning note in Home Assistant. Always check the [Kempsey Shire Council website](https://www.kempsey.nsw.gov.au/residents/waste-recycling/waste-bin-collection) for the current Christmas collection schedule.

After the holiday period it is recommended to restart the integration so the fortnightly schedule resyncs to the correct week.

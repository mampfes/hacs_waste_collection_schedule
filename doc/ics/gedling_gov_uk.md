# Gedling Borough Council (unofficial)

Gedling Borough Council (unofficial) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Gedling Borough Council does not provide bin collections in the iCal calendar format directly.
- The iCal calendar files have been generated from the official printed calendars and hosted on GitHub for use.
- Go to the Gedling Borough Council [Refuse Collection Days](https://apps.gedling.gov.uk/refuse/search.aspx) site and enter your street name to find your bin day/garden waste collection schedule. e.g. "Wednesday G2".
- Find the [required collection schedule](https://jamesmacwhite.github.io/gedling-borough-council-bin-calendars/) and use the "Copy to clipboard" button for the URL of the .ics file.

## Examples

### Monday G1 (General bin collection)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/jamesmacwhite/gedling-borough-council-bin-calendars/main/ical/gedling_borough_council_monday_g1_bin_schedule.ics
```
### Wednesday G2 (General bin collection)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/jamesmacwhite/gedling-borough-council-bin-calendars/main/ical/gedling_borough_council_wednesday_g2_bin_schedule.ics
```
### Friday G3 (General bin collection)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/jamesmacwhite/gedling-borough-council-bin-calendars/main/ical/gedling_borough_council_friday_g3_bin_schedule.ics
```
### Monday A (Garden waste collection)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/jamesmacwhite/gedling-borough-council-bin-calendars/main/ical/gedling_borough_council_monday_a_garden_bin_schedule.ics
```
### Wednesday C (Garden waste collection)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/jamesmacwhite/gedling-borough-council-bin-calendars/main/ical/gedling_borough_council_wednesday_c_garden_bin_schedule.ics
```
### Friday E (Garden waste collection)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/jamesmacwhite/gedling-borough-council-bin-calendars/main/ical/gedling_borough_council_friday_e_garden_bin_schedule.ics
```

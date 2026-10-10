# Westmorland & Furness Council

Westmorland & Furness Council is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.westmorlandandfurness.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule>, enter your postcode and select your address.
- Right click -> copy the link address of the `Add to iCalendar` link. It looks like `https://www.westmorlandandfurness.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule/download/<UPRN>`.
- Use this link as the `url` parameter. (If you know your UPRN, you can just replace the last part of the url with it.)
- This works for all former districts (Barrow-in-Furness, Eden and South Lakeland). The old `barrowbc.gov.uk` and `southlakeland.gov.uk` calendar links no longer work.
- The calendar covers about one year and contains a reminder entry `Download your bin collection calendar` at its end.

## Examples

### Eden - 1 Field House Gardens, Penrith, CA11 9EZ

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.westmorlandandfurness.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule/download/10070525889
```
### Barrow - 12 Gleaston Avenue, Barrow-in-Furness, LA13 0BP

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.westmorlandandfurness.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule/download/36022299
```
### South Lakeland - 1 Cliff Terrace, Kendal, LA9 4JR

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.westmorlandandfurness.gov.uk/bins-recycling-and-street-cleaning/waste-collection-schedule/download/100110337546
```

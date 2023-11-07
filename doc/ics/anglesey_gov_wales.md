# Anglesey

Anglesey is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.anglesey.gov.wales/en/Residents/Bins-and-recycling/Waste-Collection-Day.aspx> go to `Find your bin day` and search your address.  
- Copy the link(s) below `Download calendar to your device`
- Replace the `url` in the example configuration with this link.
- For multiple calendars (waste + garden) add a new source for each calendar.

## Examples

### LL65 1LF waste

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.anglesey.gov.wales/documents/Docs-en/Bins-and-recycling/calendars/ics/B1-1.ics
```
### LL65 1LF gerden

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.anglesey.gov.wales/documents/Docs-en/Bins-and-recycling/calendars/ics/G1-1.ics
```

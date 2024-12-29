# London Borough of Merton (New)

London Borough of Merton (New) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://fixmystreet.merton.gov.uk/waste> and enter your post code, and on the following page select your address.
- In the _Download your collection schedule_ panel, click `Add to your calendar`.
- Click the `Copy` button in _Step 1: copy the link to the calendar_.
- Use the copied link as the `url` parameter.

## Examples

### Address with Garden Waste subscription

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://fixmystreet.merton.gov.uk/waste/4273584/calendar.ics
```

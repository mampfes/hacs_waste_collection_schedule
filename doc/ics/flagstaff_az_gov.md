# City of Flagstaff, AZ

City of Flagstaff, AZ is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to https://www.recyclebycity.com/flagstaff/schedule and enter your address.
- Scroll down to the "Add to your calendar" section
- Right click Google Calendar button and select "Copy link address"
- Replace the `url` in the example configuration with this link.

## Examples

### City Hall

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: http://www.recyclebycity.com/flagstaff/schedule/cbfbefb8b9ae737c7b389baa4bfa80e5/subscribe
```

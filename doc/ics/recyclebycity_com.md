# Recycle By City

Recycle By City is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- The approach below currently only works for Flagstaff and Chicago, as the other Recycle By City cities do not support the calendar on this page.
- Go to https://www.recyclebycity.com/ and select your city
- Navigate to "Get your recycling and trash pickup schedules" and enter your address.
- Scroll down to the "Add to your calendar" section
- Right click Google Calendar button and select "Copy link address"
- Use this URL as the `url` parameter.

## Examples

### Flagstaff City Hall

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: http://www.recyclebycity.com/flagstaff/schedule/cbfbefb8b9ae737c7b389baa4bfa80e5/subscribe
```
### Chicago

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.recyclebycity.com/chicago/schedule/e757bdb2b5a35ed18704e444714a93a3/subscribe
```

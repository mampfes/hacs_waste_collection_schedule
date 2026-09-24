# ReCollect (JSON API)

Support for schedules provided by [ReCollect (JSON API)](https://recollect.net).

Source for municipalities on the ReCollect (Routeware) platform, via its JSON events API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: recollect_net
      args:
        place_id: PLACE_ID
        service_id: SERVICE_ID
        locale: LOCALE
```

### Configuration Variables

**place_id**  
*(string) (required)*

**service_id**  
*(string) (required)*

**locale**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: recollect_net
      args:
        place_id: CD149A08-1F87-11E2-A81F-CD0EC465FF45
        service_id: '224'
```

## How to get the source arguments

Look up your address in your municipality's ReCollect widget and click 'Get a calendar' to show the calendar link, e.g. https://recollect.a.ssl.fastly.net/api/places/<place_id>/services/<service_id>/events.en.ics. Enter the two IDs from that link. Use this source when that ICS link fails in the ICS source.

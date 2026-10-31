# Ray Whelan

Support for schedules provided by [Ray Whelan](https://www.raywhelan.ie).

Source for Ray Whelan recycling collection weeks, Ireland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: raywhelan_ie
      args:
        calendar: CALENDAR
        day: DAY
```

### Configuration Variables

**calendar**  
*(string) (required)*

**day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: raywhelan_ie
      args:
        calendar: GB
        day: Monday
```

## How to get the source arguments

Open https://www.raywhelan.ie/ and choose Collection Calendars. Select the GB or T calendar assigned to your route and enter your usual collection day. Ask Ray Whelan if you do not know your route. Only the recycling dates in the blue weeks are supported. The PDFs do not give dated general-waste or organic collections, or specific holiday replacements; check provider notices for changes.

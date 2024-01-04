# Abfuhrkalender Nürnberger Land

Support for schedules provided by <https://abfuhrkalender.nuernberger-land.de>.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nuernberger_land_de
      args:
        id: ID
```

### Configuration Variables

**id**
_(integer) (required)_ : The unique 11-digit identifier of your street section

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nuernberger_land_de
      args:
        id: 88-14592001
```

## How to get the source arguments

1. Open <https://abfuhrkalender.nuernberger-land.de/#waste_calendar/calendar>.
2. Fill out the filter fields on the page.
3. Right click the button "Termine in den Kalender importieren" and select "Copy link address". You should get something like this `https://abfuhrkalender.nuernberger-land.de/waste_calendar/ical?id=88-14592001&filter=rm:bio:p:dsd:poison`
4. Copy the id number out of the link to your configuration file.

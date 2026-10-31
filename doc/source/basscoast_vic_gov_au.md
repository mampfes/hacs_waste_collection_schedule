# Bass Coast Shire Council

Support for schedules provided by [Bass Coast Shire Council](https://www.basscoast.vic.gov.au).

Source for Bass Coast Shire Council (Victoria) kerbside bin calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: basscoast_vic_gov_au
      args:
        zone: ZONE
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**zone**  
*(string) (required)*

**collection_day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: basscoast_vic_gov_au
      args:
        zone: '1'
        collection_day: Wednesday
```

## How to get the source arguments

Open the bin calendar of your zone on https://www.basscoast.vic.gov.au/services/waste-rubbish/kerbside-bin-collection; the foot of the calendar lists the collection day of every suburb of the zone. Choose the zone and that day.

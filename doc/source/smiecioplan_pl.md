# SmiecioPlan

Support for schedules provided by [SmiecioPlan](https://smiecioplan.pl).

Source for SmiecioPlan.pl waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: smiecioplan_pl
      args:
        city: CITY
        street: STREET
        house: HOUSE
        building_type: BUILDING_TYPE
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house**  
*(string) (required)*

**building_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: smiecioplan_pl
      args:
        city: szczecin
        street: ALEJA WOJSKA POLSKIEGO
        house: '2'
```

## How to get the source arguments

Go to [smiecioplan.pl](https://smiecioplan.pl) and search for your address. Use the city (szczecin, gdansk, gdynia or sopot), the street name in uppercase and the house number. Some addresses (e.g. in Gdynia) have separate schedules for single-family (`single`) and multi-family (`multi`) buildings; leave `building_type` empty if your address only has one schedule.

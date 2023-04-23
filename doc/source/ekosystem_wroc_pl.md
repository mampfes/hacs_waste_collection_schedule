# Ekosystem Wrocław

Support for schedules provided by [Ekosystem](https://ekosystem.wroc.pl/) for Wrocław, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ekosystem_wroc_pl
      args:
        location_id: LOCATION
```

### Configuration Variables

**location_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ekosystem_wroc_pl
      args:
        location_id: 650358
```

## How to get the source arguments

Visit the [Ekosystem schedules search](https://ekosystem.wroc.pl/gospodarowanie-odpadami/harmonogram-wywozu-odpadow/) page and search for your address and get the schedule.  The URL should contain your location id as parameter called `lokalizacja`.

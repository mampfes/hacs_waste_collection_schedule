# Wrocław

Support for schedules provided by [Wrocław](https://ekosystem.wroc.pl).

Source for ekosystem.wroc.pl for Wrocław, Poland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ekosystem_wroc_pl
      args:
        location_id: LOCATION_ID
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

Visit the Ekosystem schedule search (https://ekosystem.wroc.pl/gospodarowanie-odpadami/harmonogram-wywozu-odpadow/), search for your address and get the schedule. The URL contains your location id as the parameter `lokalizacja`.

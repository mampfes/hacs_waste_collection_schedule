# localcities.ch

Generic source for waste collection schedules from [localcities.ch](https://www.localcities.ch) (Switzerland). Supports any Swiss municipality that publishes its waste calendar on the localcities.ch platform.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: localcities_ch
      args:
        municipality: MUNICIPALITY
        municipality_id: MUNICIPALITY_ID
        zone: ZONE
```

### Configuration Variables

**municipality**
*(string) (required)*

The municipality name as it appears in the localcities.ch URL.

**municipality_id**
*(string) (required)*

The numeric ID from the localcities.ch URL.

**zone**
*(string) (required)*

Your collection zone or locality name, as shown on the calendar page.

## How to find your arguments

1. Go to [localcities.ch](https://www.localcities.ch) and search for your municipality's waste calendar.
2. The URL will be in the format: `https://www.localcities.ch/de/entsorgung/{municipality}/{municipality_id}`
3. On the calendar page, note the zone/locality name shown next to each collection entry.

## Examples

### Volketswil - Hegnau

```yaml
waste_collection_schedule:
  sources:
    - name: localcities_ch
      args:
        municipality: volketswil
        municipality_id: 529
        zone: "Hegnau"
```

### Grenchen - Zone Ost

```yaml
waste_collection_schedule:
  sources:
    - name: localcities_ch
      args:
        municipality: grenchen
        municipality_id: 3533
        zone: "Zone Ost"
```

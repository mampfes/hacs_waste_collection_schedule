# ZVO Entsorgung - Zweckverband Ostholstein

Support for schedules provided by [ZVO](https://www.zvo.com), serving the Ostholstein district in Schleswig-Holstein, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zvo_com
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**
*(string) (required)*

The city/town name as shown on the ZVO website.

**street**
*(string) (optional)*

The street name. Not required for smaller towns that have a single collection schedule.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zvo_com
      args:
        city: "Bad Schwartau"
        street: "Lindenstraße"
```

## How to find your city and street

Search for your address at the [ZVO Abfuhrkalender](https://www.zvo.com/abfuhrkalender2026).

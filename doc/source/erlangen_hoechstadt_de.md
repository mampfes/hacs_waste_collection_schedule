# Erlangen-Höchstadt
Support for Landkreis [Erlangen-Höchstadt]() located in Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: erlangen_hoechstadt_de
      args:
        city: CITY
        street: STREET
  separator: " / "
```
Note: Set the `separator` to `" / "` as it's the way different waste types are separated in one calendar event.

### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (required)*
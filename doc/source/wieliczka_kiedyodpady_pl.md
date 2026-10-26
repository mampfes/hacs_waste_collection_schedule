# Wieliczka Kiedy Odpady (Deprecated)

Support for schedules provided by [Wieliczka Kiedy Odpady (Deprecated)](https://wieliczka.kiedyodpady.pl).

Source for Wieliczka Kiedy Odpady schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wieliczka_kiedyodpady_pl
      args:
        city: CITY
        street: STREET
        number: NUMBER
        lookahead_days: LOOKAHEAD_DAYS
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

**number**  
*(string) (optional)*

**lookahead_days**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wieliczka_kiedyodpady_pl
      args:
        city: Wieliczka (miasto)
        street: ul. Adama Asnyka
        number: "pozosta\u0142e"
```

## How to get the source arguments

This source name remains deprecated; prefer kiedyodpady_pl with municipality=wieliczka. Existing city, street and number arguments remain unchanged. Copy them from the public Wieliczka address selector. The default lookahead remains 35 days. Types now use the canonical platform vocabulary; update filters and customisations using old labels. Combined metals/plastics dates yield both canonical categories.

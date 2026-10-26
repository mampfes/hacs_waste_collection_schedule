# Grosswangen

Support for schedules provided by [Grosswangen](https://www.grosswangen.ch).

Waste collection calendar for Grosswangen, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grosswangen_ch
      args:
        route: ROUTE
```

### Configuration Variables

**route**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grosswangen_ch
      args:
        route: Innentour
```

## How to get the source arguments

Choose your refuse route: Aussentour (default), Innentour, or Sigerswil. Other collection types use the municipality-wide dates printed in the calendar. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

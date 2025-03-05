# Municipality of Dinhard Waste Collection

## Description
This source retrieves the official waste collection dates for the municipality of Dinhard directly from the official iCalendar feeds.
The following waste types are supported:

- Regular waste collection (with holiday adjustments)
- Organic waste collection ("Grüngutabfuhr")
- Paper and cardboard collection

## Configuration
No arguments required.

### Example YAML Configuration
```yaml
waste_collection_schedule:
  sources:
    - name: dinhard_ch
      args: {}
```
# Odense Renovation (iCal)

Odense Renovation (iCal) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://odenserenovation.dk> and search for your address in the collection calendar ("Mit Odense Renovation").
- Use the calendar subscription option ("Tilføj til kalender") to generate your personal iCal link. It looks like `https://mit.odenserenovation.dk/api/Calendar/GetICalCalendar?addressNo=12345678`.
- Use this link as the `url` parameter.

## Examples

### Holmstrupvej 2B

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "T\xF8mning af (.+?)\\s+p\xE5\\s+.*"
        split_at: ',\s*'
        url: https://mit.odenserenovation.dk/api/Calendar/GetICalCalendar?addressNo=119490
```

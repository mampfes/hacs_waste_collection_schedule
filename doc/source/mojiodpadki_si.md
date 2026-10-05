# Moji odpadki, Ljubljana

Support for schedules provided by [Moji odpadki, Ljubljana](https://www.mojiodpadki.si).

Source script for mojiodpadki.si

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mojiodpadki_si
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mojiodpadki_si
      args:
        uprn: '1049'
```

## How to get the source arguments

Search your address at https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov. The UPRN is the last part of the address of the schedule page (`.../urniki-odvoza-odpadkov/s/<uprn>`).

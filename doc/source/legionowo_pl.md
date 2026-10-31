# Legionowo

Support for schedules provided by [Legionowo](https://legionowo.pl/harmonogramy-odpady/).

Source for Legionowo, Poland waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: legionowo_pl
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: legionowo_pl
      args:
        street: Senatorska
```

## How to get the source arguments

Enter your street as listed on https://legionowo.pl/harmonogramy-odpady/ (for example 'Senatorska'). Where a street is split by house number, include the range exactly as shown, such as 'Aleja Legionów do nr 75' or 'Aleja Legionów od nr 76'. Accents and a leading 'ul.' are ignored.

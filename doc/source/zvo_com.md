# ZVO Entsorgung - Zweckverband Ostholstein

Support for schedules provided by [ZVO Entsorgung - Zweckverband Ostholstein](https://www.zvo.com).

Source for ZVO waste collection schedule in Ostholstein, Germany.

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

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zvo_com
      args:
        city: Bad Schwartau
        street: "Lindenstra\xDFe"
```

## How to get the source arguments

Find your city and street at https://www.zvo.com/abfuhrkalender2026. Some smaller towns do not require a street.

# PreZero

Support for schedules provided by [PreZero](https://abfallkalender.prezero.network).

Source for PreZero waste collection calendar

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallkalender_prezero_network
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        city: CITY
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallkalender_prezero_network
      args:
        street: "Aalstra\xDFe"
        house_number: '1'
```

## How to get the source arguments

Enter your street and house number. This source currently only supports Bad Oeynhausen.

# Stadt Ansbach

Support for schedules provided by [Stadt Ansbach](https://www.ansbach.de).

Source for Stadt Ansbach (city), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_ansbach_de
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
    - name: stadt_ansbach_de
      args:
        street: "Feuchtwanger Stra\xDFe"
```

## How to get the source arguments

Enter the street exactly as listed on https://www.ansbach.de/B%C3%BCrger/Umwelt-Natur/Abfall-Recycling/Abfuhrpl%C3%A4ne (e.g. 'Feuchtwanger Straße'). For the districts Bernhardswinden, Brodswinden, Claffheim, Elpersdorf, Höfstetten, Kaltengreuth, Meinhardswinden, Neuses, Obereichenbach and Schalkhausen enter the district name instead.

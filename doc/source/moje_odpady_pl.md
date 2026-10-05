# App Moje Odpady

Support for schedules provided by [App Moje Odpady](https://moje-odpady.pl/).

Source for App Moje Odpady.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moje_odpady_pl
      args:
        city: CITY
        voivodeship: VOIVODESHIP
        address: ADDRESS
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**voivodeship**  
*(string) (optional)*

**address**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: moje_odpady_pl
      args:
        city: "Aleksandr\xF3w"
        voivodeship: "woj. \u015Bl\u0105skie"
```

## How to get the source arguments

Enter the city as listed in the Moje Odpady app. If several cities share the name, also enter the voivodeship (for example 'woj. mazowieckie'). Cities that are split into streets additionally need the address (street) and, where the street has several entries, the house number.

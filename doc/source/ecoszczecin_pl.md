# EcoSzczecin

Support for schedules provided by [EcoSzczecin](https://ecoszczecin.pl).

Source for waste collection schedules in Szczecin, Poland, provided by ecoszczecin.pl.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ecoszczecin_pl
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ecoszczecin_pl
      args:
        street: TCZEWSKA
        house_number: 7A
```

## How to get the source arguments

Open https://ecoszczecin.pl/harmonogramy/, choose your street and house number from the dropdowns, and enter their values as shown. The street is not case-sensitive.

# Västervik Miljö & Energi

Support for schedules provided by [Västervik Miljö & Energi](https://www.vmeab.se/).

Source for Västervik Miljö & Energi.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vmeab_se
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vmeab_se
      args:
        city: Odensvi
        street: Ringsfall 1
```

## How to get the source arguments

Enter your city and your street address with the house number, as you would on https://www.vmeab.se/tjanster/avfall--atervinning/min-sophamtning/, e.g. city `Odensvi` and street `Ringsfall 1`.

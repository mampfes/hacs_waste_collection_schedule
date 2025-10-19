# Gmina Zgierz

Support for schedules provided by [Gmina Zgierz](https://gminazgierz.pl/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_zgierz_pl
      args:
        location_name: "Dębniak"
```

### Configuration Variables

**location_name**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_zgierz_pl
      args:
        location_name: "Dębniak"
```

## How to get the source arguments

You have to provide your location name.
You can check all the available locations in Gmina Zgierz by accessing the [website](https://bip.gminazgierz.pl/a,58674,harmonogram-odbioru-odpadow-z-terenu-gminy-zgierz-na-2025-rok.html).
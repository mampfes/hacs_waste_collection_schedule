# Métropole Nice Côte d'Azur

Support for schedules provided by [Métropole Nice Côte d'Azur](https://www.nicecotedazur.org).

Source for Métropole Nice Côte d'Azur household waste and packaging collection days (communes with a fixed weekly schedule only; bulky waste and glass are not included).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nice_cotedazur_fr
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nice_cotedazur_fr
      args:
        municipality: Aspremont
```

## How to get the source arguments

Select your commune. Only communes of the Métropole with one fixed set of collection weekdays are supported; communes with alternating weeks, seasonal periods or per-district rounds are not. Household waste and packaging (yellow bin) are included; bulky waste and glass are not.

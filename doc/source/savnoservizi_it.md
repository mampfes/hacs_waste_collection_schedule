# Savno Servizi

Support for schedules provided by [Savno Servizi](https://www.savnoservizi.it).

Source for Savno Servizi (Treviso, Veneto) collection calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: savnoservizi_it
      args:
        comune: COMUNE
```

### Configuration Variables

**comune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: savnoservizi_it
      args:
        comune: "Oderzo \u2013 zona 3"
```

## How to get the source arguments

Enter your comune as listed on https://www.savnoservizi.it/it/avvisi-e-download/download/calendari after 'per il comune di', including the zone where there is one, for example `Oderzo – zona 3`.

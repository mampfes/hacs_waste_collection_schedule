# Consorzio Area Vasta Medio Novarese

Support for schedules provided by [Consorzio Area Vasta Medio Novarese](https://www.consorziomedionovarese.it).

Source for Consorzio Area Vasta Medio Novarese (Novara), Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: consorziomedionovarese_it
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
    - name: consorziomedionovarese_it
      args:
        municipality: Ameno
```

## How to get the source arguments

Enter your municipality as listed on https://www.consorziomedionovarese.it/it-it/rifiuti/rifiuti/calendario without the year, including the zone where there is one, e.g. 'Ameno' or 'Borgomanero (zona A)'.

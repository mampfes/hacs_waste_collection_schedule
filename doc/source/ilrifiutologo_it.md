# Il Rifiutologo

Support for schedules provided by [Gruppo Hera](https://www.gruppohera.it/offerte-e-servizi/casa/ambiente), all schedules are provided by the platform [Il Rifiutologo](https://www.ilrifiutologo.it/casa_rifiutologo).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ilrifiutologo_it
      args:
        town: Comune
        street: Indirizzo
        house_number: Civico
```

### Configuration Variables

**town**  
*(String) (required)*  
City name

**street**  
*(String) (required)*  
Street name without house number

**house_number**  
*(Integer | String) (required)*  
House number

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ilrifiutologo_it
      args:
        town: Faenza
        street: Via Augusto Righi
        house_number: 6
```

## How to get the source argument

If you have any problem finding your address search it on [Il Rifiutologo](https://www.ilrifiutologo.it/casa_rifiutologo) and then copy it and paste it in your configs as it is.

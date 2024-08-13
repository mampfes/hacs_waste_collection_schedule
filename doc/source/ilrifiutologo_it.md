# Il Rifiutologo

Support for schedules provided by [Gruppo Hera](https://www.gruppohera.it/offerte-e-servizi/casa/ambiente), all schedules are provided by the platform [Il Rifiutologo](https://www.ilrifiutologo.it/casa_rifiutologo).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ilrifiutologo_it
      args:
        comune: Comune
        indirizzo: Indirizzo
        civico: Civico
```

### Configuration Variables

**comune**  
*(String) (required)*  
City name

**indirizzo**  
*(String) (required)*  
Street name without house number

**civico**  
*(Integer | String) (required)*  
House number

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ilrifiutologo_it
      args:
        comune: Faenza
        indirizzo: Via Augusto Righi
        civico: 6
```

## How to get the source argument

If you have any problem finding your address search it on [Il Rifiutologo](https://www.ilrifiutologo.it/casa_rifiutologo) and then copy it and paste it in your configs as it is.

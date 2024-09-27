# Iren Ambiente

Support for schedules provided by [Iren Ambiente](https://servizi.irenambiente.it/), serving multiple municipalities in Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: irenambiente_it
      args:
        city: CITY (Comune)
        street: STREET (Via/Piazza/Corso)
        house_number: "HOUSE NUMBER (N° civico)"
        
```

### Configuration Variables

**city**  
*(String) (required)*

**street**  
*(String) (required)*

**house_number**  
*(String|Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: irenambiente_it
      args:
        city: Torino
        street: Corso Quintino Sella
        house_number: "133"
        
```

## How to get the source argument

You can check if your address works by testing the arguments on the Iren Ambiente website: [https://servizi.irenambiente.it/](https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html). The arguments should be written exactly as autocompleted by the website.

# Iren Ambiente

Support for schedules provided by [Iren Ambiente](https://servizi.irenambiente.it/).

Source for Iren Ambiente.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: irenambiente_it
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: irenambiente_it
      args:
        city: Torino
        street: Corso Quintino Sella
        house_number: 133
```

## How to get the source arguments

Make sure your arguments are exactly spelled as shown in the autocomplete suggestions of the Iren Ambiente website: https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html

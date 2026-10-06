# Isontina Ambiente

Support for schedules provided by [Isontina Ambiente](https://isontinambiente.it).

Source for isontina ambiente, serving the municipalities of the Gorizia province (Italy) and others in the Isontina Ambiente network.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: isontinambiente_it
      args:
        address_id: ADDRESS_ID
```

### Configuration Variables

**address_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: isontinambiente_it
      args:
        address_id: 1172
```

## How to get the source arguments

Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/>, pick your municipality from the list, and select your address. The address ID is the number at the end of the URL. e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` the address ID is `1172`.

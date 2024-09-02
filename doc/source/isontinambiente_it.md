# isontina ambiente Ronchi dei legionari

Support for schedules provided by [isontina ambiente](https://isontinambiente.it), serving Ronchi dei legionari, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: isontinambiente_it
      args:
        address_id: "ADDRESS ID (indirizzo)"
        
```

### Configuration Variables

**address_id**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: isontinambiente_it
      args:
        address_id: "1172"
```

## How to get the source argument

Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari> and select your address. The address ID is the number at the end of the URL. e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` the address ID is `1172`.

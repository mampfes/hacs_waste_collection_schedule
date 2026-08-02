# Isontina Ambiente

Support for schedules provided by [Isontina Ambiente](https://isontinambiente.it), serving the municipalities of the Gorizia province (Italy) and others in the Isontina Ambiente network.

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

Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/>, pick your municipality from the list, and select your address. The address ID is the number at the end of the URL. e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/ronchi-dei-legionari/?indirizzo=1172` the address ID is `1172`.

Note: the municipality name in the URL is only used to display the address list on the website; the `address_id` alone determines which schedule is returned, so this single source works for every municipality served by Isontina Ambiente, including:

- Capriva del Friuli
- Cormons
- Doberdò del Lago
- Dolegna del Collio
- Duino Aurisina
- Farra d'Isonzo
- Fogliano Redipuglia
- Gorizia
- Gradisca d'Isonzo
- Grado
- Mariano del Friuli
- Medea
- Monfalcone
- Monrupino
- Moraro
- Mossa
- Romans d'Isonzo
- Ronchi dei Legionari
- Sagrado
- San Canzian d'Isonzo
- San Floriano del Collio
- San Lorenzo Isontino
- San Pier d'Isonzo
- Savogna d'Isonzo
- Sgonico - Zgonik
- Staranzano
- Turriaco
- Villesse

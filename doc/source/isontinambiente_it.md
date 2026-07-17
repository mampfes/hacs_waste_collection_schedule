# Isontina Ambiente

Support for schedules provided by [Isontina Ambiente](https://isontinambiente.it), serving municipalities in the province of Gorizia, Italy:

Capriva del Friuli, Cormons, Doberdò del Lago, Dolegna del Collio, Farra d'Isonzo, Fogliano Redipuglia, Gorizia, Gradisca d'Isonzo, Grado, Mariano del Friuli, Medea, Monfalcone, Monrupino, Moraro, Mossa, Romans d'Isonzo, Ronchi dei Legionari, Sagrado, San Canzian d'Isonzo, San Floriano del Collio, San Lorenzo Isontino, San Pier d'Isonzo, Savogna d'Isonzo, Sgonico - Zgonik, Staranzano, Turriaco, Villesse.

(Duino Aurisina is not supported: it uses street-side bins rather than an address-based collection calendar.)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: isontinambiente_it
      args:
        city: "CITY SLUG"
        address_id: "ADDRESS ID (indirizzo)"
```

### Configuration Variables

**city**
*(String) (optional, default: `ronchi-dei-legionari`)*

**address_id**
*(String | Integer) (optional)*

Not required for municipalities that only have a single collection zone (no address dropdown on the municipality's page).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: isontinambiente_it
      args:
        city: "gorizia"
        address_id: "488"
```

```yaml
waste_collection_schedule:
    sources:
    - name: isontinambiente_it
      args:
        city: "villesse"
```

## How to get the source argument

Visit <https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/> and select your municipality. The `city` argument is the last part of the URL, e.g. for `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/gorizia/` the `city` is `gorizia`. If your municipality's page shows an address dropdown, also select your address there; the `address_id` is the number at the end of the URL, e.g. `https://isontinambiente.it/it/servizi/servizi-per-il-tuo-comune/gorizia/?indirizzo=488` the `address_id` is `488`. If there is no address dropdown, `address_id` can be omitted.

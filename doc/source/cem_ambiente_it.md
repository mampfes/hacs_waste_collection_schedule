# CEM Ambiente

Support for waste collection schedules provided by [CEM Ambiente](https://www.cemambiente.it) (CEM FACILE), covering municipalities in the Milano / Monza e Brianza / Lodi area of Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cem_ambiente_it
      args:
        city: "Vimodrone"
        street: "Via Aldo Moro"
```

### Configuration Variables

**city**
*(string) (required)*

The municipality (comune) served by CEM Ambiente, e.g. `Vimodrone`.

**street**
*(string) (required)*

The street name (via) as listed by CEM Ambiente for the selected municipality, e.g. `Via Aldo Moro`.

## How to find your city and street

1. Open [https://www.cemambiente.it/cemfacile/](https://www.cemambiente.it/cemfacile/) and select your municipality and street to confirm the exact spelling used by CEM Ambiente.
2. Use those exact values for `city` and `street` in your configuration.
3. If the spelling doesn't match exactly, the integration will raise an error listing the closest matching names it found for your municipality.

## Supported municipalities

Agrate Brianza, Aicurzio, Arcore, Basiano, Bellinzago Lombardo, Bellusco, Bernareggio, Borgo San Giovanni, Brugherio, Burago Di Molgora, Busnago, Bussero, Cambiago, Camparada, Caponago, Carnate, Carpiano, Carugate, Casaletto Lodigiano, Casalmaiocco, Caselle Lurani, Cassano D'Adda, Cassina De' Pecchi, Cavenago Di Brianza, Cernusco Sul Naviglio, Cerro Al Lambro, Cervignano D'Adda, Cologno Monzese, Colturano, Comazzo, Concorezzo, Cornate D'Adda, Correzzana, Dresano, Gessate, Gorgonzola, Grezzago, Inzago, Lesmo, Liscate, Macherio, Masate, Massalengo, Mediglia, Melegnano, Melzo, Merlino, Mezzago, Mulazzano, Ornago, Pantigliate, Paullo, Pessano Con Bornago, Pozzo D'Adda, Pozzuolo Martesana, Rodano, Roncello, Ronco Briantino, Salerano sul Lambro, San Zenone Al Lambro, Sant'Angelo Lodigiano, Settala, Sordio, Sulbiate, Torrevecchia Pia, Trezzano Rosa, Trezzo Sull'Adda, Tribiano, Truccazzano, Usmate Velate, Vaprio D'Adda, Vedano Al Lambro, Vignate, Villasanta, Vimercate, Vimodrone, Vizzolo Predabissi.

## Bin types returned

| Provider `tipologiaServizio` prefix | Meaning | Icon |
|---|---|---|
| UMI | Raccolta Umido (food/organic waste) | `Icons.BIO_KITCHEN` |
| VER | Raccolta Verde (garden waste) | `Icons.GARDEN` |
| CAR | Raccolta Carta (paper) | `Icons.PAPER` |
| VET | Raccolta Vetro (glass) | `Icons.GLASS` |
| MUL | Raccolta Multipak (plastic + metal packaging) | `Icons.PLASTIC_PACKAGING` |
| APL | Raccolta Altre Plastiche (other plastics) | `Icons.PLASTIC_PACKAGING` |
| SEC | Raccolta Secco (residual/general waste) | `Icons.GENERAL_WASTE` |
| ECU / STP | Raccolta Ecuosacco (branded residual-waste bag) | `Icons.GENERAL_WASTE` |
| MAN / SPA / CES / MER | Street sweeping, litter-bin emptying, market cleaning (not household collection) | no icon |

The returned collection type (`t`) is the human-readable description reported by CEM Ambiente (e.g. `raccolta UMIDO`, `Spazzamento manuale`), not the prefix itself.

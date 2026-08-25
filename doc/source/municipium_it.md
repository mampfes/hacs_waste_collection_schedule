# Municipium

Support for waste collection schedules published through the [Municipium](https://www.municipiumapp.it) app (Maggioli S.p.A.), used by many Italian municipalities for their door-to-door (porta a porta) collection calendar.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: municipium_it
      args:
        municipality: "Serrastretta"
        area: "Zona 2"
```

### Configuration Variables

**municipality**
*(string) (required)*

The municipality (comune) as it appears in the Municipium app, e.g. `Serrastretta`. If the same name exists in more than one province, the integration raises an error listing the matches with their province so you can tell them apart.

**area**
*(string | integer) (optional)*

The collection zone. Only needed when the municipality has more than one zone (many have a single one). You can pass:

- the full zone name, e.g. `Utenza Domestica - Zona 2 - Frazioni Angoli, Migliuso, Cancello ed altri`,
- a unique part of it, e.g. `Zona 2` or `Migliuso`, or
- the numeric calendar id, e.g. `10326`.

If the municipality has several zones and `area` is omitted (or doesn't match), the integration raises an error listing the available zone names.

## How to find your municipality and area

1. Open the Municipium app (or your comune's Municipium page) and go to the waste section (*Rifiuti*).
2. Note the name of your comune and, if asked to choose one, your collection zone (*zona* / *utenza*).
3. Use those values for `municipality` and `area`. Partial names are matched, so `Zona 2` is usually enough.

## Supported municipalities

Any Italian municipality on the Municipium platform that has published a waste calendar is supported — the source resolves the comune against the platform's own directory at runtime, so it is not limited to a fixed list. The `EXTRA_INFO` list in the source (currently Serrastretta, CZ) only advertises verified coverage in the README and can be extended as more comuni are confirmed.

## Bin types returned

The returned collection type (`t`) is the category name reported by Municipium for that comune (e.g. `Umido`, `Vetro`, `Plastica/Lattine`). Category names differ between municipalities, so icons are assigned by matching a keyword in the name:

| Keyword in category name | Icon |
|---|---|
| umido, organico | `Icons.BIO_KITCHEN` |
| secco, indifferenziato, residuo | `Icons.GENERAL_WASTE` |
| carta, cartone | `Icons.PAPER` |
| vetro | `Icons.GLASS` |
| plastica | `Icons.PLASTIC_PACKAGING` |
| lattine, metallo | `Icons.METAL` |
| multimateriale | `Icons.RECYCLING` |
| verde, sfalci, vegetale | `Icons.GARDEN` |

Any category whose name matches no keyword is returned without an icon.

# Geovest

Support for waste collection schedules provided by [Geovest](https://geovest.bluemilk.dev), Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geovest_it
      args:
        address_name: "via antonio gramsci"
        calendar_type_id: "1"
```

### Configuration Variables

**address_name**
*(string) (required)*

Street name or address.

**numbers**
*(string) (optional)*

Street number or house number. Defaults to `1` when omitted.

**calendar_type_id**
*(string) (required)*

Use `1` for private addresses or `2` for businesses.

**days**
*(integer) (optional)*

Number of days ahead to fetch. Defaults to `30`.

## How to find your address

1. Choose your town from the Geovest source menu.
2. Search your street name.
3. Leave `numbers` empty to use the default value `1`, or enter a house number if multiple addresses are returned.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: geovest_it
      args:
        address_name: "via oreste vancini"
        calendar_type_id: "1"
        days: 30
```

## Bin types returned

| Provider description | Returned type | Icon |
|---------------------|---------------|------|
| Verde leggero | Verde leggero | `Icons.GARDEN` |
| Verde | Verde | `Icons.GARDEN` |
| Organico | Organico | `Icons.BIO_KITCHEN` |
| Umido | Umido | `Icons.BIO_KITCHEN` |
| Indifferenziato | Indifferenziato | `Icons.GENERAL_WASTE` |
| Rifiuti indifferenziati | Rifiuti indifferenziati | `Icons.GENERAL_WASTE` |
| Carta | Carta | `Icons.PAPER` |
| Cartone | Cartone | `Icons.PAPER` |
| Imballaggi in plastica | Imballaggi in plastica | `Icons.PLASTIC_PACKAGING` |
| Plastica | Plastica | `Icons.PLASTIC_PACKAGING` |
| Metalli | Metalli | `Icons.METAL` |
| Vetro | Vetro | `Icons.GLASS` |

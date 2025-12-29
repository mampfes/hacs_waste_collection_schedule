# PreZero

Support for schedules provided by [PreZero](https://abfallkalender.prezero.network).

Currently supported cities:
- **Bad Oeynhausen** - [abfallkalender.prezero.network/bad-oeynhausen](https://abfallkalender.prezero.network/bad-oeynhausen)
- **Willich** - [abfallkalender.prezero.network/willich](https://abfallkalender.prezero.network/willich)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallkalender_prezero_network
      args:
        street: STREET_NAME
        house_number: HOUSE_NUMBER
        # city: bad-oeynhausen  # Optional, defaults to bad-oeynhausen
```

### Configuration Variables

**street**
*(string) (required)*

Street name as shown on the PreZero website. The name must match exactly, including any special characters or umlauts.

**house_number**
*(string) (required)*

House number as a string (e.g., "1", "12a").

**city**
*(string) (optional)*

City identifier from the PreZero URL. Defaults to `bad-oeynhausen`. Supported values: `bad-oeynhausen`, `willich`.

## Examples

### Bad Oeynhausen (default)

```yaml
waste_collection_schedule:
  sources:
    - name: abfallkalender_prezero_network
      args:
        street: Aalstraße
        house_number: "1"
```

### Willich

```yaml
waste_collection_schedule:
  sources:
    - name: abfallkalender_prezero_network
      args:
        street: Aachener Straße
        house_number: "1"
        city: willich
```

## How to Find Your Configuration

### For Bad Oeynhausen
1. Go to [https://abfallkalender.prezero.network/bad-oeynhausen](https://abfallkalender.prezero.network/bad-oeynhausen)
2. Enter your street name and house number on the website to verify they are correct
3. Use these exact values in your configuration (the city parameter is already set to Bad Oeynhausen by default)

### For Willich
1. Go to [https://abfallkalender.prezero.network/willich](https://abfallkalender.prezero.network/willich)
2. Enter your street name and house number on the website to verify they are correct
3. Use these exact values in your configuration with `city: willich`

## Waste Types

The integration supports various waste types, including:

- **Biotonne** (organic waste bin)
- **Gelbe Tonne** (yellow bin - recyclables)
- **Restmülltonne** (residual waste bin)
- **Papiertonne** (paper bin)
- **Schadstoffsammlung** (hazardous waste collection)

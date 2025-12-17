# PreZero Bad Oeynhausen

Support for schedules provided by [PreZero Bad Oeynhausen](https://abfallkalender.prezero.network/bad-oeynhausen).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bad_oeynhausen
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

City identifier from the PreZero URL. Defaults to `bad-oeynhausen`. Only needed if using this source for another PreZero city.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bad_oeynhausen
      args:
        street: Aalstraße
        house_number: "1"
```

Or with explicit city parameter:

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bad_oeynhausen
      args:
        street: Aalstraße
        house_number: "1"
        city: bad-oeynhausen
```

## How to Find Your Configuration

1. Go to [https://abfallkalender.prezero.network/bad-oeynhausen](https://abfallkalender.prezero.network/bad-oeynhausen)
2. Enter your street name and house number on the website to verify they are correct
3. Use these exact values in your configuration (the city parameter is already set to Bad Oeynhausen by default)

## Note

This source is specifically configured for Bad Oeynhausen. If PreZero supports other cities with the same system, the source may work for them as well by changing the `city` parameter.

## Waste Types

The integration supports various waste types, including:

- **Biotonne** (organic waste bin)
- **Gelbe Tonne** (yellow bin - recyclables)
- **Restmülltonne** (residual waste bin)
- **Papiertonne** (paper bin)
- **Schadstoffsammlung** (hazardous waste collection)

# OLO

Support for schedules provided by [OLO](https://www.olo.sk/), serving in Bratislava, Slovakia.

These waste types are supported:

- Zmesový komunálny odpad (Mixed waste)
- Kuchynský bioodpad (Kitchen bio waste)
- Záhradný bioodpad (Garden bio waste)
- Plast, kovy a nápojové kartóny (Plastic, metals and beverage cartons)
- Papier (Paper)
- Sklo (Glass)

## Configuration via configuration.yaml

You can configure this source using either a **registration number** OR a **street name**. At least one is required.

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        registrationNumber: NUMBER
```

OR

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: STREET
```

### Configuration Variables

**registrationNumber**
*(String) (optional)*

Your OLO registration number. If provided, this is used for a direct lookup (recommended).

**street**
*(String) (optional)*

Street name and number. Used for search-based lookup if registration number is not provided.

## Examples

### Using registration number (recommended)

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        registrationNumber: 1353013
```

### Using street name

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: Jantarova 47
```

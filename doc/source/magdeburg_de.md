# Städtischer Abfallwirtschaftsbetrieb Magdeburg (SAB)

Support for schedules provided by [SAB Magdeburg](https://www.magdeburg.de), serving the city of Magdeburg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: magdeburg_de
      args:
        street: STREET
```

### Configuration Variables

**street**
*(string) (required)*

The street name and house number (e.g. `Halberstädter Chaussee 66`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: magdeburg_de
      args:
        street: "Halberstädter Chaussee 66"
```

## How to find your street

Search for your address at the [SAB Magdeburg Abfuhrkalender](https://sab.ssl.metageneric.de/app/sab_i_tp/index.php). Use the street name and house number exactly as shown in the dropdown.

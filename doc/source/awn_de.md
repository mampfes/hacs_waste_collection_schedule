# Abfallwirtschaft Neckar-Odenwald-Kreis

Support for schedules provided by [Abfallwirtschaft Neckar-Odenwald-Kreis](https://www.awn-online.de).

Source for AWN (Abfallwirtschaft Neckar-Odenwald-Kreis).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awn_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**address_suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awn_de
      args:
        city: Adelsheim
        street: Badstr.
        house_number: 1
```

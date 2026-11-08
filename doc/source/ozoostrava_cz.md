# OZO Ostrava

Support for schedules provided by [OZO Ostrava](https://ozoostrava.cz).

Waste collection schedules for Ostrava and nearby municipalities

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ozoostrava_cz
      args:
        obec: OBEC
        obvod: OBVOD
        ulice: ULICE
        cislo: CISLO
```

### Configuration Variables

**obec**  
*(string) (required)*

**obvod**  
*(string) (required)*

**ulice**  
*(string) (required)*

**cislo**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ozoostrava_cz
      args:
        obec: Ostrava
        obvod: Poruba
        ulice: Hlavní třída
        cislo: '583'
```

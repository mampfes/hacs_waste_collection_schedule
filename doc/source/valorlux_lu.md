# Valorlux

Support for Valorlux PMC collections.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: valorlux_lu
      args:
        city: CITY
        zone: ZONE
```

### Arguments

**city**  
*(string) (required)*

The name of your city or municipality.

**zone**  
*(string) (optional)*

Some cities are split into multiple collection zones (e.g., Luxembourg). Check the [Valorlux website](https://www.valorlux.lu/fr/trier-mes-dechets/calendrier-de-collecte) to see if your city requires a zone.
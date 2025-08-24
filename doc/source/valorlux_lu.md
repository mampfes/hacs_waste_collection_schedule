# Valorlux

Support for generic Valorlux collections.

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

**zone**  
*(string) (optional)*

Some cities are split into multiple collection zones (e.g., Luxembourg). Check the [Valorlux website](https://www.valorlux.lu/fr/trier-mes-dechets/mon-calendrier-de-collecte) to see if your city requires a zone.

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

The name of your city or municipality. This will be a dropdown list in the UI.

**zone**  
*(string) (optional)*

Some cities are split into multiple collection zones (e.g., Luxembourg, Differdange). If your city has zones, a dropdown will appear. You can find your correct zone on the [Valorlux website](https://www.valorlux.lu/fr/trier-mes-dechets/calendrier-de-collecte).

# Mirabel (QC)

Support for schedules provided by [Mirabel (QC)](https://mirabel.ca/collectes).

Source script for mirabel.ca/collectes

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mirabel_ca
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mirabel_ca
      args:
        zone: 1
```

## How to get the source arguments

You can find your collection zone number (1 to 8) using the webpage: https://mirabel.ca/services/services-en-ligne/trouver-ma-zone-de-collecte

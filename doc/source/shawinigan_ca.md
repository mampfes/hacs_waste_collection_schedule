# Shawinigan (QC)

Waste collection schedules provided by [Ville de Shawinigan](https://geoweb.shawinigan.ca/CollecteMatieresResiduelles/) via their ArcGIS REST MapServer.

## Supported collection types

| Type | Description |
|------|-------------|
| `RECYCLAGE` | Blue bin (bi-weekly) |
| `ORDURES` | Grey bin (regular) |
| `COMPOST` | Green bin |
| `SAPIN` | Christmas tree collection (seasonal) |
| `FEUILLES` | Leaf collection (seasonal) |

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: shawinigan_ca
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Street address including city and postal code.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: shawinigan_ca
      args:
        address: "1760 Avenue de la Paix, Shawinigan, QC G9N 6H7"
```

## How to find your address

Enter your full civic address as you would in Google Maps. Including the postal code improves geocoding accuracy. The source uses Esri's World geocoder to convert the address to coordinates, then queries the city's MapServer to determine your collection districts.

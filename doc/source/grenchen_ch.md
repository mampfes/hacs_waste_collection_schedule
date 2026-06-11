# Grenchen (CH)

> **Deprecated:** This source is deprecated. Please use [localcities.ch](/doc/source/localcities_ch.md) instead with `municipality: grenchen` and `municipality_id: 3533`.

Support for waste collection schedules in Grenchen, Switzerland, via [localcities.ch](https://www.localcities.ch/de/entsorgung/grenchen/3533).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grenchen_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)* Collection zone: `Zone Ost` or `Zone West`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grenchen_ch
      args:
        zone: "Zone Ost"
```

## How to get the source arguments

Visit the [Grenchen waste calendar](https://www.localcities.ch/de/entsorgung/grenchen/3533) to find your collection zone.

Collection types:

- **Grünabfälle** (green waste)
- **Karton** (cardboard)
- **Altpapier** (waste paper)
- **Altglas** (glass)
- **Altmetall** (scrap metal)

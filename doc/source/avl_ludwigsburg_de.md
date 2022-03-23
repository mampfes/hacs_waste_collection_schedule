# AVL Ludwigsburg

Support for schedules provided by [avl-ludwigsburg.de](https://www.avl-ludwigsburg.de) located in Baden Württemberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: avl_ludwigsburg
      args:
        city: Ludwigsburg
        street: Bahnhofstraße
```

### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (optional - depending on city)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: avl_ludwigsburg
      args:
        street: Bahnhofstraße
        city: Ludwigsburg
      customize:
        - type: LVP 4-Rad
          alias: Gelber Sack 4-Rad
          show: true
        - type: LVP
          alias: Gelber Sack
          show: true
        - type: Papier
          alias: Papier
          show: true
        - type: Papier 4-Rad
          alias: Papier 4-Rad
          show: true
        - type: Restmüll 4-Rad
          alias: Restmüll 4-Rad
          show: true
        - type: Restmüll
          alias: Restmüll
          show: true
        - type: Biomüll
          alias: Biomüll
          show: true
        - type: Glas
          alias: Glas
          show: true
```

Use `sources.customize` to filter or rename the waste types:

```yaml
waste_collection_schedule:
  sources:
    - name: avl_ludwigsburg
      args:
        street: Bahnhofstraße
        city: Ludwigsburg
      customize:
        - type: LVP 4-Rad
          alias: Gelber Sack 4-Rad
          show: true
        - type: LVP
          alias: Gelber Sack
          show: true
        - type: Papier
          alias: Papier
          show: true
        - type: Papier 4-Rad
          alias: Papier 4-Rad
          show: true
        - type: Restmüll 4-Rad
          alias: Restmüll 4-Rad
          show: true
        - type: Restmüll
          alias: Restmüll
          show: true
        - type: Biomüll
          alias: Biomüll
          show: true
        - type: Glas
          alias: Glas
          show: true

sensor:
  # Nächste Müllabholung
  - platform: waste_collection_schedule
    name: Nächste Leerung
    
  # Nächste Papier Leerung
  - platform: waste_collection_schedule
    name: Nächste Papier Leerung
    types:
      - Papier
      
  # Nächste Papier 4-Rad Leerung
  - platform: waste_collection_schedule
    name: Nächste Papier 4-Rad Leerung
    types:
      - Papier 4-Rad
      
  # Nächste gelber Sack Abholung
  - platform: waste_collection_schedule
    name: Nächste Gelber Sack Abholung
    types:
      - Gelber Sack

  # Nächste gelber Sack Abholung
  - platform: waste_collection_schedule
    name: Nächste Gelber Sack 4-Rad Abholung
    types:
      - Gelber Sack 4-Rad

  # Nächste Restmüll Abholung
  - platform: waste_collection_schedule
    name: Nächste Restmüll Leerung
    types:
      - Restmüll

  # Nächste Restmüll 4-Rad Abholung
  - platform: waste_collection_schedule
    name: Nächste Restmüll 4-Rad Leerung
    types:
      - Restmüll 4-Rad
      
  # Nächste Biomüll Abholung
  - platform: waste_collection_schedule
    name: Nächste Biomüll Leerung
    types:
      - Biomüll

  # Nächste Glas Abholung
  - platform: waste_collection_schedule
    name: Nächste Glas Abholung
    types:
      - Glas
```

## How to get the source arguments

Check [avl-ludwigsburg.de Abfallkalender](https://www.avl-ludwigsburg.de/privatkunden/termine/abfallkalender/) if you only need the city e.g. Möglingen or if you need an additional street name e.g. in Ludwigsburg.
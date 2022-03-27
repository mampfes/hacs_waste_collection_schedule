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

## How to get the source arguments

Check [avl-ludwigsburg.de Abfallkalender](https://www.avl-ludwigsburg.de/privatkunden/termine/abfallkalender/) if you only need the city e.g. Möglingen or if you need an additional street name e.g. in Ludwigsburg.
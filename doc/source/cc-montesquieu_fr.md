# Communauté de Communes de Montesquieu

Support for schedules provided by [Communauté de Communes de Montesquieu](https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets), serving french cities :

- Ayguemorte-les-Graves
- Beautiran
- Cabanac-et-Villagrains
- Cadaujac
- Castres-Gironde
- Isle Saint-Georges
- La Brède
- Léognan
- Martillac
- Saint-Médard-d’Eyrans
- Saint-Morillon
- Saint-Selve
- Saucats.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cc-montesquieu_fr
      args:
        commune: <commune from the list>
```

### Configuration Variables

**commune**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cc-montesquieu_fr
      args:
        commune: Martillac
```

## How to get the source argument

Use the cities list or visit [https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets](https://www.cc-montesquieu.fr/vivre/dechets/collectes-des-dechets) and look for your city.

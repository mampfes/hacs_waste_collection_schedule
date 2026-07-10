# Terres Touloises

Support for schedules provided by [Terres Touloises](https://www.terrestouloises.com/terres-touloises-au-quotidien/gestion-des-dechets/collectes-des-ordures-menageres-et-recyclables/), serving french communes:

- Aingeray
- Andilly
- Ansauville
- Avrainville
- Bicqueley
- Bois-de-Haye
- Boucq
- Bouvron
- Bruley
- Charmes-la-Côte
- Chaudeney-sur-Moselle
- Choloy-Ménillot
- Domèvre-en-Haye
- Domgermain
- Dommartin-lès-Toul
- Écrouves
- Fontenoy-sur-Moselle
- Foug
- Francheville
- Gondreville
- Grosrouvres
- Gye
- Jaillon
- Lagney
- Laneuveville-derrière-Foug
- Lay-Saint-Rémy
- Lucey
- Manoncourt-en-Woëvre
- Manonville
- Ménil-la-Tour
- Minorville
- Noviant-aux-Prés
- Pagney-derrière-Barine
- Pierre-la-Treiche
- Royaumeix
- Sanzey
- Tremblecourt
- Trondes
- Villey-le-Sec
- Villey-Saint-Étienne.

Note: Toul is not supported by this source. Unlike every other commune above, the town of Toul is itself split into several street-level collection zones (Saint-Michel Briffoux, Saint Mansuy, Croix de Metz, Saint Èvre), each with a different calendar, and this source cannot disambiguate between them from the commune name alone. Residents of Toul should refer directly to the [collection webpage](https://www.terrestouloises.com/terres-touloises-au-quotidien/gestion-des-dechets/collectes-des-ordures-menageres-et-recyclables/) for their zone.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: terrestouloises_com
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
    - name: terrestouloises_com
      args:
        commune: Bois-de-Haye
```

## How to get the source argument

Use the commune list above or visit [the collection webpage](https://www.terrestouloises.com/terres-touloises-au-quotidien/gestion-des-dechets/collectes-des-ordures-menageres-et-recyclables/) and look for your commune.

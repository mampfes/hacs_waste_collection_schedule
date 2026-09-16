# Rennes Métropole

Support for waste collection schedules provided by [Rennes Métropole](https://dechets.metropole.rennes.fr), France.

Rennes Métropole publishes one collection calendar per town (and one per quarter inside the city of Rennes) as a PDF. This source reads the calendars that are linked from the [collection calendar page](https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/), so it keeps working when the calendars are replaced with a new edition every autumn.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: metropole_rennes_fr
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**
*(String) (required)*

Name of the town, or of the Rennes quarter, whose calendar should be used.

## How to find your `commune`

1. Open <https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/>.
2. Scroll to the sections *Calendriers des collectes à Rennes* and *Calendriers des collectes (hors Rennes)*.
3. Find the entry covering your address and use its name as `commune`.

Notes:

- Several towns often share one calendar, for example `Bruz - Chavagne`. The name of your own town on its own (`Chavagne`) is enough — you do not have to type the whole entry.
- Inside the city of Rennes, calendars are published per quarter. Use the full quarter name (`Q7 - La Pommeraie`) or simply the quarter number (`Q7`).
- Accents and upper/lower case are ignored, so `cesson-sevigne` also works.
- If the name cannot be matched, the integration raises an error listing all names that are currently published.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: metropole_rennes_fr
      args:
        commune: "Cesson-Sévigné"
```

Rennes quarter:

```yaml
waste_collection_schedule:
  sources:
    - name: metropole_rennes_fr
      args:
        commune: "Q7 - La Pommeraie"
```

## Bin types returned

| Provider description | Returned type | Icon |
|---------------------|---------------|------|
| Bac gris (ordures ménagères) | `Ordures ménagères` | `Icons.GENERAL_WASTE` |
| Bac jaune (déchets recyclables) | `Déchets recyclables` | `Icons.RECYCLING` |

Collection days are read from the highlighted rows of the published calendar, so shifts caused by public holidays (for example the collection moved from Wednesday 11 November to Thursday 12 November) and weeks without any collection (weeks 53 and 1) are handled automatically.

## Notes

- The calendars run from October to September. While a new edition is already published but not yet in effect, this source additionally reads the previous edition so that the upcoming collections are not missing.
- Glass, food waste and bulky waste are brought to collection points or to a recycling centre in Rennes Métropole and are therefore not part of the published collection calendar.

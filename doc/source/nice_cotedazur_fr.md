# Métropole Nice Côte d'Azur

Support for collection schedules published by [Métropole Nice Côte d'Azur](https://www.nicecotedazur.org/services/dechets/collecte-et-tri-dechets/jours-et-horaires-de-collecte/), France.

Phase 1 covers fixed-day household-waste schedules for 15 municipalities. Schedules involving alternating weeks, seasonal periods, or geographic sectors are intentionally not approximated.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nice_cotedazur_fr
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(String) (required)*

Accepted values:

- `Aspremont`
- `Beaulieu-sur-Mer`
- `Cap d'Ail`
- `Castagniers`
- `Colomars`
- `Èze`
- `Falicon`
- `La Trinité`
- `Le Broc`
- `Nice`
- `Saint-Blaise`
- `Saint-Jean-Cap-Ferrat`
- `Saint-Laurent-du-Var`
- `Saint-Martin-du-Var`
- `Villefranche-sur-Mer`

Bulky waste is collected by appointment and glass is collected through bring banks; neither is included by this source.

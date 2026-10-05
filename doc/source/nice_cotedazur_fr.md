# Nice Côte d'Azur (France)

This source provides fixed-day household-waste collection schedules published by Métropole Nice Côte d'Azur.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: nice_cotedazur_fr
      args:
        municipality: Nice
```

The source currently supports fixed-day schedules for Aspremont, Beaulieu-sur-Mer, Cap d'Ail, Castagniers, Colomars, Èze, Falicon, La Trinité, Le Broc, Nice, Saint-Blaise, Saint-Jean-Cap-Ferrat, Saint-Laurent-du-Var, Saint-Martin-du-Var, and Villefranche-sur-Mer.

Schedules involving alternating weeks, seasonal periods, or geographic sectors are intentionally not interpreted. Bulky waste and glass collection are not included.

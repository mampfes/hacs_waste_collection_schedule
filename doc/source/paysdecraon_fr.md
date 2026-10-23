# Communauté de Communes du Pays de Craon

Support for schedules provided by [Communauté de Communes du Pays de Craon](https://www.paysdecraon.fr).

Source for the Communauté de Communes du Pays de Craon (Mayenne), France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: paysdecraon_fr
      args:
        weekday: WEEKDAY
        commune: COMMUNE
```

### Configuration Variables

**weekday**  
*(string) (required)*

**commune**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: paysdecraon_fr
      args:
        weekday: mercredi
        commune: "Saint-Michel-de-la-Ro\xEB"
```

## How to get the source arguments

The Pays de Craon calendar only shows whether a week is a household waste or a packaging week. Choose the weekday on which your bins are usually collected; collections are shifted by one day after public holidays. Optionally enter your municipality (as printed in the calendar) to also get its branch shredding (broyage de branches) date.

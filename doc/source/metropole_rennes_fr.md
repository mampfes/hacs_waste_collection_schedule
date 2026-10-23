# Rennes Métropole

Support for schedules provided by [Rennes Métropole](https://dechets.metropole.rennes.fr).

Source for Rennes Métropole, France.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: metropole_rennes_fr
      args:
        commune: "Cesson-S\xE9vign\xE9"
```

## How to get the source arguments

Open https://dechets.metropole.rennes.fr/ou-et-comment-jeter-vos-dechets/ and look at the lists of collection calendars. Use the name of the entry covering your address as `commune`, for example `Cesson-Sévigné`. If several towns share one calendar (for example `Bruz - Chavagne`), the name of your own town is enough. Inside the city of Rennes, use the quarter, for example `Q7 - La Pommeraie` or just `Q7`.

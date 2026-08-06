# Clisson Sèvre et Maine Agglo

Support for schedules provided by [Clisson Sèvre et Maine Agglo](https://environnement.clissonsevremaine.fr), serving the 18 municipalities of the agglomeration in the Loire-Atlantique department, France.

Two waste streams are collected door-to-door and reported by this source:

- `Ordures ménagères` (residual household waste)
- `Emballages` (recyclable packaging)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: clissonsevremaine_fr
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: clissonsevremaine_fr
      args:
        commune: Maisdon-sur-Sèvre - zone 1
```

## How to get the source argument

Open the [collection calendar page](https://environnement.clissonsevremaine.fr/dechets/collecte-des-dechets/calendrier-des-collectes) and pick your municipality in the drop-down menu. Use the wording shown there; matching is case- and accent-insensitive.

Several municipalities are split into collection zones, and one street in Clisson has its own round. The maps at the end of the downloadable PDF calendars, linked from the same page, tell you which zone your street belongs to.

Accepted values:

- `Aigrefeuille-sur-Maine`
- `Boussay`
- `Château-Thébaud`
- `Clisson`
- `Clisson, rue Saint-Antoine`
- `Gétigné - zone A`
- `Gétigné - zone B`
- `Gorges`
- `Haute-Goulaine`
- `La Haye-Fouassière - Zone A`
- `La Haye-Fouassière - Zone B`
- `La Planche`
- `Maisdon-sur-Sèvre - zone 1`
- `Maisdon-sur-Sèvre - zone 2`
- `Maisdon-sur-Sèvre - zone 3`
- `Monnières`
- `Remouillé`
- `Saint-Hilaire-de-Clisson - Zone A`
- `Saint-Hilaire-de-Clisson - Zone B`
- `Saint-Lumine-de-Clisson - Zone A`
- `Saint-Lumine-de-Clisson - Zone B`
- `St-Fiacre-sur-Maine`
- `Vieillevigne`

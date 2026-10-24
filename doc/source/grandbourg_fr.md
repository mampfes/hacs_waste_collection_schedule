# Grand Bourg Agglomération

Support for schedules provided by [Grand Bourg Agglomération](https://www.grandbourg.fr).

Source for the Grand Bourg Agglomération (Ain) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grandbourg_fr
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
    - name: grandbourg_fr
      args:
        commune: Courtes
```

## How to get the source arguments

Enter your commune (or commune sector) as listed under the collection calendars on https://www.grandbourg.fr/26-collecte-des-ordures-menageres.htm, for example `Courtes` or `Attignat Est Crangeat`.

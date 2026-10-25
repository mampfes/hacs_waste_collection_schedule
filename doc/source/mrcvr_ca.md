# MRC de La Vallée-du-Richelieu

Support for schedules provided by [MRC de La Vallée-du-Richelieu](https://www.mrcvr.ca).

Source for the MRC de La Vallée-du-Richelieu (Québec) collection calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mrcvr_ca
      args:
        municipalite: MUNICIPALITE
```

### Configuration Variables

**municipalite**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mrcvr_ca
      args:
        municipalite: Otterburn Park
```

## How to get the source arguments

Enter your municipality as listed on https://www.mrcvr.ca/services/matieres-residuelles/calendriers-des-collectes/, for example `Otterburn Park`.

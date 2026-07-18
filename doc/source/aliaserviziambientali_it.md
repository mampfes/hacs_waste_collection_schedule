# Alia Servizi Ambientali S.p.A.

Support for schedules provided by [Alia Servizi Ambientali S.p.A.](https://www.aliaserviziambientali.it).

Source for Alia Servizi Ambientali S.p.A..

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aliaserviziambientali_it
      args:
        municipality: MUNICIPALITY
        area: AREA
```

### Configuration Variables

**municipality**  
*(string) (required)*

**area**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aliaserviziambientali_it
      args:
        municipality: Gambassi Terme
```

## How to get the source arguments

Visit <https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti> and select your municipality. If you see an embedded calendar you can just use the municipality name and leave the area empty. If you see a list of areas, follow the link to the area calendar; there you can find the area ID in the URL, for example: `https://differenziata.junker.app/embed/barberino-tavarnelle/area/67333/calendario` the area ID is `67333`.

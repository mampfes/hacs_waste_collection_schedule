# Alia Servizi Ambientali S.p.A.

Support for schedules provided by [Alia Servizi Ambientali S.p.A.](https://www.aliaserviziambientali.it), serving multiple municipalities, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: aliaserviziambientali_it
      args:
        municipality: MUNICIPALITY (Comune)
        area: AREA
```

### Configuration Variables

**municipality**  
*(String) (required)*

**area**  
*(Integer|String) (Optional)* see below

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: aliaserviziambientali_it
      args:
        municipality: Gambassi Terme     
```

```yaml
waste_collection_schedule:
    sources:
    - name: aliaserviziambientali_it
      args:
        municipality: Barberino Tavarnelle
        area: 67334
```

## How to get the source argument

Visit <https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti> and select your municiaplity, if you see an embedded calendar you can just use the municipality name, and leave the area empty. If you see a list of areas, you need to follow the link to the area calendar, there you can fin the area ID in the URL, for example: `https://differenziata.junker.app/embed/barberino-tavarnelle/area/67333/calendario` the area ID is `67333`.

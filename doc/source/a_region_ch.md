# A-Region, Switzerland

Support for schedules provided by [A-Region.ch](https://www.a-region.ch)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
```

### Configuration Variables

**municipality**<br>
*(string) (required)*

**district**<br>
*(string) (optional)*
Some municipalities (like Rorschach) are separated into districts for several waste types (e.g. `Hauskehricht` and `Papier, Karton`).

## Examples

Municipality without extra districts:

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        municipality: Andwil
```

Municipality with extra districts:

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        municipality: Rorschach
        district: Unteres Stadtgebiet

```

## How to get the source argument

Open [Abfallkalender A-Region](https://www.a-region.ch/index.php?apid=13875680&apparentid=4618613) which shows a list of all municipalities. Select your municipality from the list.
Some municipalities are separated into districts. Check for all waste types and add district if needed.

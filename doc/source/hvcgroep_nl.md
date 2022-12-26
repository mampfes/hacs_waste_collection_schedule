# HVCGroep

Support for schedules provided by [hvcgroep.nl](https://www.hvcgroep.nl/) and other Dutch municipalities.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
        service: SERVICE
```

### Configuration Variables

**postal_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**service**  
*(string) (optional, default="hvcgroep")*

Use one of the following codes as service code:

- alphenaandenrijn
- cranendonck
- cyclusnv
- dar
- denhaag
- gad
- gemeenteberkelland
- hvcgroep
- lingewaard
- middelburgvlissingen
- mijnblink
- peelenmaas
- prezero
- purmerend
- rmn
- schouwen-duiveland
- spaarnelanden
- stadswerk072
- sudwestfryslan
- venray
- voorschoten
- waalre
- zrd

## Example

```yaml
# hvgroep
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: 1713VM
        house_number: 1
        service: hvxgroep
```

```yaml
# cyclusnv
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: 2841ML
        house_number: 1090
        service: cyclusnv
```

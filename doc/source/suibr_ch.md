# SUIBR

Support for schedules provided by [SUIBR](https://www.suibr.ch).

Source for SUIBR (Nidwalden) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: suibr_ch
      args:
        municipality: MUNICIPALITY
        street: STREET
        hnr: HNR
```

### Configuration Variables

**municipality**  
*(string) (required)*

**street**  
*(string) (optional)*

**hnr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: suibr_ch
      args:
        municipality: Beckenried
        street: Acheri
        hnr: 1
```

## How to get the source arguments

Choose your municipality and enter your street and house number as the calendar at https://www.kvvnw.sammelkalender.ch writes them. The error message lists the valid values.

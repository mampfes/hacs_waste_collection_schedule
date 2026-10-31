# Selargius Sostenibile

Support for schedules provided by [Selargius Sostenibile](https://selargiusostenibile.it).

Source for domestic waste collection in Selargius, Sardinia, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: selargiusostenibile_it
      args:
        url: URL
        zone: ZONE
        paper_area: PAPER_AREA
```

### Configuration Variables

**url**  
*(string) (required)*

**zone**  
*(string) (required)*

**paper_area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: selargiusostenibile_it
      args:
        url: https://selargiusostenibile.it/wp-content/uploads/2026/02/Calendario-SELARGIUS-26-27-UD-CENTRO-ABITATO-rev2.pdf
        zone: A
        paper_area: Selargius paese
```

## How to get the source arguments

Copy the link to the current UTENZE DOMESTICHE / CENTRO ABITATO PDF on https://selargiusostenibile.it. Find your residual-waste zone A or B in the street list at the beginning of that PDF. Independently choose Selargius paese or Su Planu e Is Corrias for paper. Update the URL when a new calendar is published. The supported layout is the March-February booklet with two months across facing pages. Oil and textiles are collected only by appointment and have no dates in this source.

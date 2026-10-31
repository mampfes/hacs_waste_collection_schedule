# Nemenčinės komunalininkas

Support for schedules provided by [Nemenčinės komunalininkas](https://www.nemenkom.lt).

Source for UAB "Nemenčinės komunalininkas" (Vilnius district) household waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nemenkom_lt
      args:
        village: VILLAGE
        street: STREET
```

### Configuration Variables

**village**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nemenkom_lt
      args:
        village: Bajorai
        street: "Melis\u0173 g."
```

## How to get the source arguments

Open the household waste schedule (XLSX) on https://www.nemenkom.lt/buitiniu-ir-pakuociu-atlieku-surinkimo-grafikas/ and copy the village name from the `Kaimai` column (the part before any brackets). If the village is split by streets, also enter your street exactly as listed in the brackets, e.g. `Melisų g.`.

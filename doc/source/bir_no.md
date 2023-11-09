# BIR

```yaml
waste_collection_schedule:
  sources:
    - name: bir_no
      args:
        street_name: ""
        house_number: ""
        house_letter: ""
```

# Example configuration.yaml:

```yaml
# Waste collection
waste_collection_schedule:
  sources:
    - name: bir_no
      args:
        street_name: "Alf Bondes Veg"
        house_number: "13"
        house_letter: "B"
      customize:
        - type: blue bin
          alias: Papir
        - type: green bin
          alias: Restavfall
sensor:
  - platform: waste_collection_schedule
    name: next_collection
  - platform: waste_collection_schedule
    name: waste_collection_garbage
    details_format: upcoming
    types:
      - Restavfall
  - platform: waste_collection_schedule
    name: waste_collection_paper
    details_format: upcoming
    types:
      - Papir og plastemballasje
```
# BIR - Bergensområdets Interkommunale Renovasjonsselskap

```yaml
waste_collection_schedule:
  sources:
    - name: bir_no
      args:
        street_name: ""
        house_number: ""
        house_letter: ""
```

### Configuration Variables

**street_name**  
*(string) (required)*

**house_number**  
*(string|Integer) (required)*

**house_letter**  
*(string) (optional)*

The arguments should be written exactly like on the <https://bir.no/> website

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

# Optional Sensors
  sensors:
    - name: next_collection
    - name: waste_collection_garbage
      details_format: upcoming
      types:
        - Restavfall
    - name: waste_collection_paper
      details_format: upcoming
      types:
        - Papir og plastemballasje
```

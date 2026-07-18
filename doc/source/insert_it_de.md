# Insert IT Apps

Support for schedules provided by [Insert IT Apps](https://insert-infotech.de/).

Source for Apps by Insert IT

## Configuration via configuration.yaml

### Using location_id

```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: MUNICIPALITY
        location_id: LOCATION_ID
```

### Using street and hnr

```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: MUNICIPALITY
        street: STREET
        hnr: HNR
```

### Configuration Variables

**municipality**  
*(string) (required)*

**location_id**  
*(string) (alternative)*

**street**  
*(string) (alternative)*

**hnr**  
*(string) (alternative)*

Provide one of: `location_id` or `street` + `hnr`.

## Example

### Using location_id

```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: Offenbach
        location_id: 7036
```

### Using street and hnr

```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: Offenbach
        street: "Kaiserstra\xDFe"
        hnr: 1
```

# Offenbach.de 


## offenbach_de source is deprecated, please use [insert_it_de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/insert_it_de.md) as new source.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: offenbach_de
      args:
        f_id_location: LocationID
```

### Configuration Variables

**f_id_location**  
*(integer) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: offenbach_de
      args:
        f_id_location: 7036
```
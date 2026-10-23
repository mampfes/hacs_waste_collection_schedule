# SICA

Support for schedules provided by [SICA](https://sica.lu).

Source script for sica.lu served municipalities

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sica_lu
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sica_lu
      args:
        municipality: habscht
```

## How to get the source arguments

Enter the name of your municipality as listed by SICA, e.g. 'Steinfort', 'Habscht' or 'Mamer'. A wrong name lists the valid ones.

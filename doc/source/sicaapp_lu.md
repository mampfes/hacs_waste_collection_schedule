# SICA

Support for schedules provided by [SICA](https://sicaapp.lu/), serving multiple, Luxembourg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sicaapp_lu
      args:
        commune: COMMUNE
        
```

### Configuration Variables

**commune**  
*(String) (required)*

Use one of:

- Bertrange
- Garnich
- Kehlen
- Koerich
- Kopstal
- Mamer
- Steinfort
- Habscht

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sicaapp_lu
      args:
        commune: Steinfort
        
```

## How to get the source argument

Find the parameter of your address using [https://sicaapp.lu/](https://sicaapp.lu/) and write them exactly like on the web page.

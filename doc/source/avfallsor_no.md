# Avfall Sør, Kristiansand

Support for schedules provided by [Avfall Sør, Kristiansand](https://avfallsor.no/), serving Kristiansand, Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: avfallsor_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: avfallsor_no
      args:
        address: Auglandslia 1, Kristiansand
        
```

## How to get the source argument

Visit [https://avfallsor.no/henting-av-avfall/finn-hentedag/](https://avfallsor.no/henting-av-avfall/finn-hentedag/) and write the address exactly like suggested by the input field.

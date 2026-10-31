# Silea

Support for schedules provided by [Silea](https://www.sileaspa.it).

Silea

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: silea_it
      args:
        municipality: MUNICIPALITY
        address: ADDRESS
```

### Configuration Variables

**municipality**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: silea_it
      args:
        municipality: Lomagna
        address: via martiri
```

## How to get the source arguments

Enter your municipality and street as listed at https://www.sileaspa.it. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

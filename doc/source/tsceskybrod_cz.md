# Technické služby Český Brod

Support for schedules provided by [Technické služby Český Brod](https://www.tsceskybrod.cz/), serving Český Brod, Czech Republic.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tsceskybrod_cz
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tsceskybrod_cz
      args:
        street: Kollárova
```

## How to get the source argument

Visit [https://www.tsceskybrod.cz/pravidelny-svoz-odpadu](https://www.tsceskybrod.cz/pravidelny-svoz-odpadu) and enter the street or location name exactly as listed in the table.

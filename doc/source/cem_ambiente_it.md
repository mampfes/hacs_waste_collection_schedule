# CEM Ambiente

Support for schedules provided by [CEM Ambiente](https://www.cemambiente.it).

Source for CEM Ambiente (CEM FACILE), covering municipalities in the Milano / Monza e Brianza / Lodi area of Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cem_ambiente_it
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cem_ambiente_it
      args:
        city: Vimodrone
        street: Via Aldo Moro
```

## How to get the source arguments

Enter the municipality (comune) and street (via) exactly as they are known to CEM Ambiente, e.g. as shown on https://www.cemambiente.it/cemfacile/. If the exact spelling isn't found, the error message will list the closest matching street names for your municipality.

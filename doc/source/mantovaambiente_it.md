# Mantova Ambiente

Support for schedules provided by [Mantova Ambiente](https://www.mantovaambiente.it).

Source for Mantova Ambiente (Gruppo TEA), Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mantovaambiente_it
      args:
        comune: COMUNE
        zona: ZONA
```

### Configuration Variables

**comune**  
*(string) (required)*

**zona**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mantovaambiente_it
      args:
        comune: Gonzaga
        zona: Zona 1
```

## How to get the source arguments

Enter your municipality as it is named on https://www.mantovaambiente.it (e.g. Gonzaga). If the municipality is split into several collection zones, also enter your zone (e.g. Zona 1): on the municipality's page, the link "Non conosci la zona?" lists the streets and hamlets of each zone. Leave the zone empty for a municipality with a single zone; if it has several, the form then lists them.

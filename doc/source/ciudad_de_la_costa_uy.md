# Municipio de Ciudad de la Costa

Support for schedules provided by [Municipio de Ciudad de la Costa](https://www.imcanelones.gub.uy).

Source for household waste (general and recyclables) collection in Ciudad de la Costa, Canelones, Uruguay.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ciudad_de_la_costa_uy
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ciudad_de_la_costa_uy
      args:
        address: De los Pinos, Ciudad de la Costa
```

## How to get the source arguments

Enter your street address in Ciudad de la Costa. Include the neighbourhood for common street names. The published municipal zone map supplies collection weekdays. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

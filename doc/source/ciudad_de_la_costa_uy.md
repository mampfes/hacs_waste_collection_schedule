# Municipio de Ciudad de la Costa

Support for waste collection schedules provided by the [Municipio de Ciudad de la Costa](https://www.imcanelones.gub.uy) (Canelones, Uruguay), based on the municipality's [published collection zone map](https://www.google.com/maps/d/u/0/viewer?mid=17F0VsWkN9V7hoqMSyQ_H2_rl0SYLlZel).

Your address is geocoded (via OpenStreetMap/Nominatim) and matched against the "RECOLECCIÓN DE RESIDUOS" zone polygons published on the municipality's map to determine the weekly collection days for general ("mezclados") and recyclable ("reciclables") waste.

**Note:** garden/pruning waste collection ("Recolección de restos vegetales") is not currently supported by this source, as the upstream map describes those schedules in inconsistent free text (week-of-month rules) that could not be reliably parsed. General household waste and recycling are fully supported.

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

Street address (house number and street, or just the street name) within Ciudad de la Costa. If your street name is common to multiple neighbourhoods (barrios), include the neighbourhood name for a more accurate match.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ciudad_de_la_costa_uy
      args:
        address: De los Pinos, Ciudad de la Costa
```

## How to get the source arguments

Enter your street address as you would search for it on a map, e.g. `1901 Cuba, Ciudad de la Costa` or just the street name, e.g. `De los Pinos, Ciudad de la Costa`. You can cross-check your collection zone visually on the municipality's [collection map](https://www.google.com/maps/d/u/0/viewer?mid=17F0VsWkN9V7hoqMSyQ_H2_rl0SYLlZel) by enabling the "RECOLECCIÓN DE RESIDUOS" layer.

Collection types returned:

- **General** — mixed household waste, 2 days/week (morning or evening pickup, depending on zone)
- **Reciclables** — recyclables, 1 day/week

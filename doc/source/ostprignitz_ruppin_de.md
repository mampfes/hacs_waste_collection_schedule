# Ostprignitz-Ruppin

Support for schedules provided by [Ostprignitz-Ruppin](https://www.ostprignitz-ruppin.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ostprignitz_ruppin_de
      args:
        location: LOCATION
        street: STREET
```

### Configuration Variables

**location**<br>
*(string)*

The name of your municipality (Ort).

**street**<br>
*(string)*

Copy the entry exactly as shown in the "Straße" dropdown. This may include more than just the street name (e.g. house number and postal code), as in the example below.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: ostprignitz_ruppin_de
      args:
        location: Neuruppin
        street: "Am alten Gymnasium 9, 16816"
```

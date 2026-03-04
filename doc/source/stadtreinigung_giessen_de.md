# Stadtreinigung Gießen

Support for schedules provided by [Stadtreinigung Gießen](https://stadtreinigung.giessen.de/) located in Hesse, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_giessen_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

The name of the street as shown on the Stadtreinigung Gießen website.

**house_number**  
*(string) (required)*

The house number.

### How to get the source arguments

1. Go to [stadtreinigung.giessen.de/akal/akal1.php](https://stadtreinigung.giessen.de/akal/akal1.php)
2. Select the first letter of your street name using the alphabet navigation
3. Find your street in the dropdown list
4. Use the exact street name as the `street` argument
5. Use your house number as the `house_number` argument

**Note:** If you enter an invalid street name, the integration will suggest available streets starting with the same letter.

## Examples

### Achstattring 1

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_giessen_de
      args:
        street: Achstattring
        house_number: "1"
```

### Berliner Platz 5

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_giessen_de
      args:
        street: Berliner Platz
        house_number: "5"
```

### Marktplatz 10

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_giessen_de
      args:
        street: Marktplatz
        house_number: "10"
```

## Supported Waste Types

The following waste types are returned by this source:

- Restmüll (Residual waste)
- Biotonne (Organic waste)
- Altpapier (Paper)
- Gelbe Tonne (Yellow bin / Packaging)
- Astwerk (Garden waste / Branches)
- Weihnachtsbaum (Christmas tree collection)


# Landkreis Südwestpfalz

Support for schedules provided by [Landkreis Südwestpfalz](https://www.lksuedwestpfalz.de).

Source for waste collection in the Landkreis Südwestpfalz.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: suedwestpfalz_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**address_suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: suedwestpfalz_de
      args:
        city: Fischbach
        street: "Daniel-Theysohn-Stra\xDFe"
        house_number: '15'
```

## How to get the source arguments

Enter the village, street and house number exactly as the calendar at https://abfallwirtschaft.lksuedwestpfalz.de/WasteManagementSuedwestpfalz/WasteManagementServlet lists them. Village names use no umlauts (e.g. Bruchweiler-Baerenbach). Put a house number addition (e.g. A) in 'Address suffix'.

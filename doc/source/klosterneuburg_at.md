# Stadtgemeinde Klosterneuburg

Support for schedules provided by [Stadtgemeinde Klosterneuburg](https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender).

Source for Stadtgemeinde Klosterneuburg waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: klosterneuburg_at
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: klosterneuburg_at
      args:
        street: "Kierlinger Stra\xDFe"
        house_number: '10'
```

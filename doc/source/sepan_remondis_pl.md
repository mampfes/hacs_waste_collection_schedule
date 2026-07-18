# Koziegłowy/Objezierze/Oborniki

Support for schedules provided by [Koziegłowy/Objezierze/Oborniki](https://sepan.remondis.pl).

Source for Koziegłowy/Objezierze/Oborniki city garbage collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sepan_remondis_pl
      args:
        city: CITY
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sepan_remondis_pl
      args:
        city: "Pozna\u0144"
        street_name: "\u015AWI\u0118TY MARCIN"
        street_number: '2'
```

# Stadtwerke Singen

Support for schedules provided by [Stadtwerke Singen](https://www.stadtwerke-singen.de).

Source for Stadtwerke Singen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_singen_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_singen_de
      args:
        street: Im Twielfeld
```

## How to get the source arguments

Street name as listed in the Stadtwerke Singen waste calendar street directory, or one of the outlying districts (Beuren, Bohlingen, Friedingen, Hausen, Schlatt, Überlingen). House number. Only required if the street is split into several address ranges with different collection days (e.g. 'Alemannenstraße').

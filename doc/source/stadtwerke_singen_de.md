# Stadtwerke Singen

Support for schedules provided by [Stadtwerke Singen](https://www.stadtwerke-singen.de/abfall/abfallkalender/), Germany.

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

Street name as listed in the Stadtwerke Singen waste calendar street directory, or one of the outlying districts (Beuren, Bohlingen, Friedingen, Hausen, Schlatt, Überlingen).

**house_number**
*(integer) (optional)*

Only required if the street is split into several address ranges with different collection days (e.g. `Alemannenstraße`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_singen_de
      args:
        street: "Im Twielfeld"
```

```yaml
waste_collection_schedule:
  sources:
    - name: stadtwerke_singen_de
      args:
        street: "Alemannenstraße"
        house_number: 10
```

## How to get the source arguments

1. Go to the [Stadtwerke Singen Abfallkalender](https://www.stadtwerke-singen.de/abfall/abfallkalender/).
2. Click the first letter of your street (or one of the district shortcuts for Beuren, Bohlingen, Friedingen, Hausen, Schlatt or Überlingen) to see how it is listed.
3. Use that street name (without the `(Nr. ...)` suffix) as `street`.
4. If the street is listed multiple times with different `(Nr. ...)` house-number ranges, also provide your `house_number` so the correct range can be selected automatically.

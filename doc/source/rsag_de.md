# RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft

Support for schedules provided by [RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft](https://www.rsag.de).

Source for RSAG waste collection in the Rhein-Sieg-Kreis, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rsag_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rsag_de
      args:
        city: "K\xF6nigswinter"
        street: "Winzerstra\xDFe"
```

## How to get the source arguments

Visit https://www.rsag.de/abfallkalender/abfuhrtermine and select your city and street. Use the exact city and street names shown in the form.

# RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft

Support for schedules provided by [RSAG](https://www.rsag.de), serving the Rhein-Sieg-Kreis, Germany. Covered municipalities include Alfter, Bad Honnef, Bornheim, Eitorf, Hennef, Königswinter, Lohmar, Meckenheim, Much, Neunkirchen-Seelscheid, Niederkassel, Rheinbach, Ruppichteroth, Sankt Augustin, Siegburg, Swisttal, Troisdorf, Wachtberg and Windeck.

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
*(String) (required)*

Name of the city/municipality, e.g. `Königswinter`.

**street**
*(String) (required)*

Name of the street, e.g. `Winzerstraße`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rsag_de
      args:
        city: Königswinter
        street: Winzerstraße
```

## How to get the source arguments

Visit [https://www.rsag.de/abfallkalender/abfuhrtermine](https://www.rsag.de/abfallkalender/abfuhrtermine) and select your city and street from the dropdown menus. Use the city and street names exactly as shown in the form.

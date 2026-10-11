# Entsorgungsverband Völklingen (EVV)

Support for schedules provided by [Entsorgungsverband Völklingen (EVV)](https://www.evv-voelklingen.de).

Source for Entsorgungsverband Völklingen waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: evv_voelklingen_de
      args:
        ortsteil: ORTSTEIL
        strasse: STRASSE
        hausnummer: HAUSNUMMER
        behaelter: BEHAELTER
```

### Configuration Variables

**ortsteil**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (optional)*

**behaelter**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: evv_voelklingen_de
      args:
        ortsteil: "F\xFCrstenhausen"
        strasse: "Kaiserstra\xDFe"
        hausnummer: '2'
```

## How to get the source arguments

Enter the district, street and (for some streets) house number as shown in the EVV portal. `behaelter` is optional and maps a waste type name to a container size in litres (e.g. Restmüll: '240', Papier: '1100'); only the named types are filtered, the others are shown for every container size.

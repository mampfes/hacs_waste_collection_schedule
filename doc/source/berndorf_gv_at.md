# Stadtgemeinde Berndorf

Support for schedules provided by [Stadtgemeinde Berndorf](https://www.berndorf.gv.at).

Source for Stadtgemeinde Berndorf, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: berndorf_gv_at
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: berndorf_gv_at
      args:
        strasse: "Albertstra\xDFe"
        hausnummer: '1'
```

## How to get the source arguments

Open https://www.berndorf.gv.at/Buergerservice/Aktuelles/Muellabfuhrtermine, pick your street and house number from the dropdowns, and use the same values for 'strasse' and 'hausnummer'.

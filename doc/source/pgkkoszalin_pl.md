# PGK Koszalin

Support for schedules provided by [PGK Koszalin](https://www.pgkkoszalin.pl).

Source for PGK Koszalin (single-family housing), Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pgkkoszalin_pl
      args:
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**district**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pgkkoszalin_pl
      args:
        district: Raduszka
        street: "Po\u0142czy\u0144ska"
```

## How to get the source arguments

Enter your estate (osiedle) as listed on https://www.pgkkoszalin.pl/harmonogramy-wywozu-odpadow/harmonogram-miasto-koszalin/ (e.g. 'Raduszka'), and your street as printed on the estate's page (e.g. 'Gnieźnieńska 52-110 (parzyste)'). The street can be left out for an estate with a single calendar. Multi-family housing (zabudowa wielorodzinna) is not supported.

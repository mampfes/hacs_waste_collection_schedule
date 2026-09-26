# Team Orange (Landkreis Würzburg)

Support for schedules provided by [Team Orange (Landkreis Würzburg)](https://www.team-orange.info).

Source for team orange waste collection in Landkreis Würzburg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: team_orange_de
      args:
        ort: ORT
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: team_orange_de
      args:
        ort: Altertheim
        strasse: Am Berg
        hausnummer: 1
```

## How to get the source arguments

Please take Ort (municipality), Strasse (street) and Hausnummer (street number) from the calendar at https://www.team-orange.info/muellabfuhr/abfallkalender/.

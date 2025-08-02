# Landkreis Helmstedt

Support for schedules provided by [Landkreis Helmstedt](https://www.landkreis-helmstedt.de/buerger-leben/bauen-wohnen/abfallentsorgung/abfuhrkalender/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_helmstedt_de
      args:
        municipal: GEMEINDE
        restabfall: RESTABFALL_ABFUHR_GEBIET
        bioabfall: BIOABFALL_ABFUHR_GEBIET
        gelber_sack: GELBER_SACK_ABFUHR_GEBIET
        altpapier: ALTPAPIER_ABFUHR_GEBIET
```

### Configuration Variables

**municipal**  
*(String) (required)* - Name of the ICS calendar on the calendar website without year. Currently, the following values (without quotes) are valid:
- `"Grasleben und Velpke"`
- `"Schöningen und Heeseberg"`
- `"Nord-Elm und Königslutter Ortsteile"`
- `"Lehre"`
- `"Königslutter Stadtgebiet"`
- `"Helmstedt und Ortsteile"`

**restabfall** 
_(int) (required)_: Number from the PDF calendar from the calendar website for your municipal

**bioabfall** 
_(int) (required)_ : Number from the PDF calendar from the calendar website for your municipal

**gelber_sack**
_(int) (required)_ : Number from the PDF calendar from the calendar website for your municipal

**altpapier**
_(int) (required)_ : Number from the PDF calendar from the calendar website for your municipal

## Example for Rhode 2025

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_helmstedt_de
      args:
        municipal: "Nord-Elm und Königslutter Ortsteile"
        restabfall: 2
        bioabfall: 2
        gelber_sack: 1
        altpapier: 2
```

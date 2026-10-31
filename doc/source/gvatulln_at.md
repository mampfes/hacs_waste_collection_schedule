# GVA Tulln

Support for schedules provided by [GVA Tulln](https://gvatulln.at).

Source for the Gemeindeverband für Abfallwirtschaft im Raum Tulln (AT).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gvatulln_at
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
        building: BUILDING
```

### Configuration Variables

**municipality**  
*(string) (required)*

**district**  
*(string) (optional)*

**building**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gvatulln_at
      args:
        municipality: "Gro\xDFweikersdorf"
```

## How to get the source arguments

Enter your municipality as it is named on https://gvatulln.at/fuer-die-bevoelkerung/abholtermine/ (e.g. 'Tulln', 'St. Andrä-Wördern', 'Sitzenberg'). Municipalities split into collection districts also need the district: the 'Sprengel' number from the plan (e.g. '2'), or 'Zeiselmauer' / 'Wolfpassing'. Choose building type 'commercial' for businesses and apartment complexes (Gewerbe und Wohnhausanlagen).

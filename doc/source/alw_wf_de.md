# ALW Wolfenbüttel

Support for schedules provided by [ALW Wolfenbüttel](https://www.alw-wf.de//), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: alw_wf_de
      args:
        ort: ORT
        strasse: STRASSE
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: alw_wf_de
      args:
        ort: "Linden mit Okertalsiedlung"
        strasse: "Am Buschkopf"
```

## How to get the source arguments

1. Go to the calendar at https://www.alw-wf.de/index.php/abfallkalender.
2. Select your location in the drop down menus.
   - Notice: The page reloads after selecting `Ort`, so wait for that before selecting `Straße`.
3. Copy the **exact** values from the 2 drop down menus as `ort` and `strasse` in the source configuration.
   - In case you can only select the street `Alle Straßen`, then the `strasse` option does not matter (it is still required, just set it to something).

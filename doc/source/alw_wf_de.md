# ALW Wolfenbüttel

Support for schedules provided by [ALW Wolfenbüttel](https://www.alw-wf.de//), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: "wol"
        city: ORT
        street: STRASSE
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
    - name: jumomind_de
      args:
        service_id: "wol"
        city: "Linden"
        street: "Am Buschkopf"
```

## How to get the source arguments

1. Go to the [calendar](https://www.alw-wf.de/index.php/abfallkalender).
2. Select your location in the drop down menus.
   - Notice: The page reloads after selecting `Ortschaft`, so wait for that before selecting `Straßenname`.
3. Copy the **exact** values from the 2 drop down menus as `Ortschaft` and `Straßenname` in the source configuration.
   - In case you can only select the street `Alle Straßen`, then the `strasse` option does not matter (it is still required, just set it to something).

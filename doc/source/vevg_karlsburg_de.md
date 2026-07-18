# VEVG Vorpommern-Greifswald

Support for schedules provided by [VEVG Vorpommern-Greifswald](https://www.vevg-karlsburg.de).

Source for Ver- und Entsorgungsgesellschaft des Landkreises Vorpommern-Greifswald mbH (VEVG), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vevg_karlsburg_de
      args:
        ort: ORT
        kreis: KREIS
```

### Configuration Variables

**ort**  
*(string) (required)*

**kreis**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vevg_karlsburg_de
      args:
        ort: 722
        kreis: G
```

## How to get the source arguments

1. Go to the VEVG online calendar:
   - OVP (Anklam/Wolgast/Greifswald-Land): https://vevg-karlsburg.de/online-abfallkalender-ovp.html
   - JTPL (Jarmen/Tutow/Peenetal-Loitz): https://vevg-karlsburg.de/online-abfallkalender-jtpl.html
   - UHGW (Stadt Greifswald streets): https://vevg-karlsburg.de/online-abfallkalender-uhgw.html
   - UER (Uecker-Randow): https://vevg-karlsburg.de/online-abfallkalender-uer.html
2. Select your location from the dropdown and click 'Auswählen'.
3. The `ort` and `kreis` values appear in the page URL as `key={ort}#{name}#{kreis}#`.
   - Example: Wusterhusen shows `key=722#Wusterhusen#G#`, so `ort=722` and `kreis="G"`.
4. For locations marked with 'lesen' (street-level lookup): select your street first, then read ort/kreis from the resulting URL.

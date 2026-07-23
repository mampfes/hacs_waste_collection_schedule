# VEVG Vorpommern-Greifswald

Support for schedules provided by [Ver- und Entsorgungsgesellschaft des Landkreises Vorpommern-Greifswald mbH (VEVG)](https://www.vevg-karlsburg.de), serving the Landkreis Vorpommern-Greifswald, Germany.

Covers four collection areas:
- **OVP**: Anklam, Wolgast, Greifswald-Land (kreis codes: `A`, `G`, `W`, and a few others)
- **JTPL**: Jarmen, Tutow, Peenetal-Loitz (kreis code: `L`)
- **UHGW**: Stadt Greifswald streets (kreis code: `H`)
- **UER**: Uecker-Randow (kreis code: `U`)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: vevg_karlsburg_de
      args:
        ort: ORT_ID
        kreis: KREIS_CODE
```

### Configuration Variables

**ort**
*(Integer) (required)*

Numeric location ID from the VEVG online calendar dropdown. Example: `722` for Wusterhusen.

**kreis**
*(String) (required)*

Single-letter district code. Common values: `G` (Greifswald-Land), `A` (Anklam), `W` (Wolgast), `L` (JTPL), `H` (Stadt Greifswald streets), `U` (Uecker-Randow).

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

1. Open the VEVG online calendar for your area:
   - **OVP**: <https://vevg-karlsburg.de/online-abfallkalender-ovp.html>
   - **JTPL**: <https://vevg-karlsburg.de/online-abfallkalender-jtpl.html>
   - **UHGW** (Stadt Greifswald streets): <https://vevg-karlsburg.de/online-abfallkalender-uhgw.html>
   - **UER**: <https://vevg-karlsburg.de/online-abfallkalender-uer.html>

2. Select your location from the dropdown and click **Auswählen**.

3. Look at the page URL. It will contain `key={ort}#{name}#{kreis}#`. Use the first number as `ort` and the single letter as `kreis`.
   - Example: Wusterhusen shows `key=722#Wusterhusen#G#`, so `ort: 722` and `kreis: G`.

4. For locations marked with **lesen** (street-level lookup), first select your street from the secondary dropdown, then read `ort` and `kreis` from the resulting URL.

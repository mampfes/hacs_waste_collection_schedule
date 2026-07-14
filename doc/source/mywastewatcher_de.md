# myWasteWatcher (WasteWatcher.NET)

Support for schedules provided by [mywastewatcher.de](https://www.mywastewatcher.de), a WasteWatcher.NET waste-calendar platform used by municipalities on the Lower Rhine (NRW), Germany.

The default values for `oguid` and `app_path` select **Hamminkeln**, currently the only instance known to publish schedule data. The `abfallkalenderdk2` (Kalkar) and `abfallkalenderRBE` (Rheinberg) instances exist on the platform but return no schedule data for any street (as of July 2026). Other municipalities hosted on mywastewatcher.de should work by supplying their own `app_path` and `oguid` — see [How to get the source arguments](#how-to-get-the-source-arguments).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mywastewatcher_de
      args:
        ort: ORT
        strasse: STRASSE
        ortsteil: ORTSTEIL
        bemerkung: BEMERKUNG
        oguid: OGUID
        app_path: APP_PATH
```

### Configuration Variables

**strasse** *(string) (required)*: Street name exactly as shown on the website. If the street cannot be matched, the error lists all streets starting with the same letter (shown as a dropdown in the UI configuration); a picked entry like `Ackerstraße (Mehrhoog)` is accepted as-is.

**ort** *(string) (optional)*: City name exactly as shown on the website.

**ortsteil** *(string) (optional)*: District, needed when the same street name exists in multiple districts. The error message lists all matching street/district combinations if your street cannot be matched.

**bemerkung** *(string) (optional)*: Remark column from the street list (e.g. house-number ranges like `1-50`), needed when multiple entries exist for the same street.

**oguid** *(string) (optional, default: `B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F` = Hamminkeln)*: Identifier of the waste management area. Visible as the `oguid` parameter in the URL of your municipality's calendar page.

**app_path** *(string) (optional, default: `abfallkalenderdk` = Hamminkeln)*: First path segment of your municipality's calendar URL, e.g. `abfallkalenderdk` for `https://www.mywastewatcher.de/abfallkalenderdk/...`.

## Example

Hamminkeln (defaults apply):

```yaml
waste_collection_schedule:
  sources:
    - name: mywastewatcher_de
      args:
        ort: Hamminkeln
        strasse: Ackerstraße
        ortsteil: Mehrhoog
```

## How to get the source arguments

For Hamminkeln, the pre-filled defaults already fit — just enter city and street.

For another municipality on the platform:

1. Open your municipality's calendar page on [mywastewatcher.de](https://www.mywastewatcher.de) (use the link provided by your local waste authority).
2. Read `app_path` and `oguid` directly from the browser address bar: `https://www.mywastewatcher.de/<app_path>/default.aspx?oguid=<oguid>`.
3. Enter `ort` and `strasse` exactly as they appear in the dropdowns on that page. If the street dropdown shows a district (`Ortsteil`) or remark (`Bemerkung`) column for your street, provide those too.

## Notes

The waste types are reported exactly as shown on the website: a fraction code followed by the collection district (Abfuhrbezirk), e.g. `PA HAM03` = paper collection in district HAM03. The fraction codes, as defined in the website's legend:

| Code | German | English |
|---|---|---|
| RA | Restabfall | residual waste |
| BA | Bioabfall | organic waste |
| PA | Papier | paper |
| LP | Leichtverpackung | lightweight packaging (yellow bag) |
| GL | Glas | glass |
| GB | Grünschnitt | garden/green waste |
| SC | Schadstoffe (Schadstoffmobil) | hazardous waste (mobile collection) |
| SP | Sperrmüll | bulky waste |

The website's `Bemerkung` column is passed along as the collection's `description` — for `SC` entries it contains the stops and times of the Schadstoffmobil, and around holidays it flags rescheduled pickups (e.g. `Vorverlegung`). It is available in the sensor attributes (with `details_format: generic`); the calendar entity does not currently display descriptions.

Use the `customize` option to rename the sensors if desired, e.g.:

```yaml
waste_collection_schedule:
  sources:
    - name: mywastewatcher_de
      args:
        strasse: Molkereistraße
      customize:
        - type: "RA HAM03"
          alias: Restabfall
        - type: "PA HAM03"
          alias: Papier
```

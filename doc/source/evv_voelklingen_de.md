# Entsorgungsverband Völklingen (EVV)

Support for schedules provided by [Entsorgungsverband Völklingen](https://www.evv-voelklingen.de/), serving Völklingen and surrounding districts in Saarland, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: evv_voelklingen_de
      args:
        ortsteil: ORTSTEIL
        strasse: STRASSE
        hausnummer: HAUSNUMMER  # optional
```

### Configuration Variables

**ortsteil**
*(String) (required)*

District / city part as shown in the EVV portal second dropdown (e.g. `Völklingen`, `Fürstenhausen`, `Wehrden`). Umlauts must match exactly.

**strasse**
*(String) (required)*

Street name as shown in the EVV portal (e.g. `Hauptstraße`, `Poststraße`). Umlauts must match exactly.

**hausnummer**
*(String | Integer) (optional)*

House number. Required for some streets that have different schedules per house number range.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: evv_voelklingen_de
      args:
        ortsteil: Fürstenhausen
        strasse: Hauptstraße
        hausnummer: "2"
```

## How to find your parameters

1. Open the EVV citizen portal: [https://buerger-portal-voelklingen.azurewebsites.net](https://buerger-portal-voelklingen.azurewebsites.net)
2. Select your **Ortsteil** (district) from the dropdown — use exactly this spelling including umlauts.
3. Select your **Straße** (street) — use exactly this spelling.
4. Optionally note the **Hausnummer** if the portal asks for one.

If the source cannot find your `ortsteil` or `strasse`, it logs the list of valid values to the Home Assistant log so you can correct the spelling.
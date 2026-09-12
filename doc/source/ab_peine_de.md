# Landkreis Peine

Support for schedules provided by [Abfallwirtschaftsbetrieb Landkreis Peine](https://ab-peine.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ab_peine_de
      args:
        strasse: STRASSE
        ort: ORT
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name (or a unique partial match), as offered by the autocomplete on the Abfuhrtermine page after selecting your municipality.

Some municipalities, including Broistedt, provide one schedule for all streets. For these municipalities, you can use your street name or `alle Straßen`.

**ort**
*(string) (optional)*

Municipality/district from the "Ort auswählen" dropdown. Use the complete displayed name, for example `Broistedt`, `Vechelde (Hauptort)`, or `Peine-Kernstadt (mit Telgte)`.

Set this parameter for municipalities outside Peine-Kernstadt. The source resolves the selected municipality before searching for streets. Existing Peine-Kernstadt configurations without `ort` continue to work.

## Examples

Peine-Kernstadt:

```yaml
waste_collection_schedule:
  sources:
    - name: ab_peine_de
      args:
        strasse: "Gerhart-Hauptmann-Straße"
```

Broistedt:

```yaml
waste_collection_schedule:
  sources:
    - name: ab_peine_de
      args:
        strasse: "Osterriehe"
        ort: "Broistedt"
```

## How to get the source arguments

1. Go to [Abfuhrtermine Landkreis Peine](https://www.ab-peine.de/Abfuhrtermine/).
2. Select your municipality in "Ort auswählen" and copy its complete displayed name into `ort`.
3. Start typing your street name and select the matching suggestion. Use the street name as `strasse`.
4. If the suggestion applies to all streets in the municipality ("alle Straßen"), you can use your street name or `alle Straßen` as `strasse`.

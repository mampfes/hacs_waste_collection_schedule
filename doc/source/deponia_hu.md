# Depónia Nonprofit Kft.

Support for schedules provided by [Depónia Nonprofit Kft.](https://deponia.hu/telepuleskereso), serving settlements in Fejér, Veszprém and Komárom-Esztergom counties, Hungary.

Depónia does not publish an API. This source drives the public settlement search form and parses the annual hulladéknaptár PDF for the selected settlement (and street, where the form offers one).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: deponia_hu
      args:
        city: CITY_NAME
        street: STREET_NAME
```

### Configuration Variables

**city**
*(string) (required)*

Settlement name as shown on [the Depónia settlement search](https://deponia.hu/telepuleskereso) (e.g. `Aba`, `Székesfehérvár`, `Velence`).

**street**
*(string) (optional)*

Street name as shown after selecting the settlement. Required for towns that publish street-level calendars (Székesfehérvár, Veszprém, Velence, Mór, …). Copy the label exactly, including house-number ranges such as `Ady Endre utca 1-20.`. Smaller settlements (Aba, Nadap, Etyek, …) have a single city calendar and do not need this argument.

**ssl_verify**
*(boolean) (optional, default: `true`)*

Verify the HTTPS certificate. Set to `false` if Home Assistant cannot validate deponia.hu (some OpenSSL setups do not fetch the RapidSSL intermediate that browsers load automatically).

## Example

City-level calendar (no street dropdown):

```yaml
waste_collection_schedule:
  sources:
    - name: deponia_hu
      args:
        city: Aba
        ssl_verify: false
```

Street-level calendar:

```yaml
waste_collection_schedule:
  sources:
    - name: deponia_hu
      args:
        city: Székesfehérvár
        street: Fő utca
        ssl_verify: false
```

## How to get the source arguments

1. Open https://deponia.hu/telepuleskereso
2. Select your settlement
3. If an "Utca választása" dropdown appears, pick your street and use that exact label as `street`

## Supported waste types

| PDF label | Type returned |
|-----------|----------------|
| Vegyes / kommunális (weekday rule in the PDF) | Communal |
| szelektív | Selective |
| zöldhulladék | Green |
| konyhai (if present in the table) | Kitchen |

## Notes

- Mixed (`Communal`) collections are listed in the PDF as weekdays (`Vegyes hulladékgyűjtési nap: KEDD,PÉNTEK`) rather than a date table. The source expands those weekdays for the calendar year and applies holiday postponements when the PDF spells them out (e.g. *áthelyezésre kerül*).
- Some Veszprém calendars only say mixed waste is collected on "the usual days from last year" and do not name the weekdays. In that case only Selective and Green dates are returned.
- The PDF is a PowerPoint export; the parser uses `pypdf` layout extraction to keep month columns aligned.

# Siókom Nonprofit Kft.

Support for schedules provided by [Siókom Nonprofit Kft.](https://www.siokom.hu/jaratterv/), serving Siófok and surrounding settlements in Somogy and Fejér counties, Hungary.

Siókom does not publish an API. This source reads the public járatterv page and parses the annual hulladéknaptár PDF for the selected settlement or district.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: siokom_hu
      args:
        area: AREA_NAME
```

### Configuration Variables

**area**
*(string) (required)*

Settlement or district name **exactly as shown** on [the Siókom járatterv page](https://www.siokom.hu/jaratterv/). There is no street selector. Copy the short name, not the neighbourhood description under Siófok rows. Spaces around hyphens are ignored (`Siófok H-P` matches `Siófok H - P`).

Names currently listed on the járatterv page:

- `Ádánd`
- `Balatonendréd`
- `Balatonfőkajár`
- `Balatonföldvár`
- `Balatonkenese`
- `Balatonkenese vasúttól a Balatonpatig`
- `Balatonöszöd`
- `Balatonszárszó`
- `Balatonvilágos`
- `Bálványos`
- `Csajág`
- `Enying`
- `Kereki`
- `Kötcse`
- `Küngös`
- `Nagyberény`
- `Nagycsepely`
- `Nyim`
- `Pusztaszemes`
- `Ságvár`
- `Siófok Cs-v`
- `Siófok H - P`
- `Siófok K - Sz`
- `Siójut`
- `Som`
- `Szántód`
- `Szólád`
- `Teleki`
- `Zamárdi Kőhegy`
- `Zamárdi vasúttól délre`
- `Zamárdi vasúttól északra`

**ssl_verify**
*(boolean) (optional, default: `true`)*

Verify the HTTPS certificate.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: siokom_hu
      args:
        area: Balatonvilágos
```

```yaml
waste_collection_schedule:
  sources:
    - name: siokom_hu
      args:
        area: Siófok Cs-v
```

## How to get the source arguments

1. Open https://www.siokom.hu/jaratterv/
2. Find your settlement or district in the list
3. Copy that short label into `area`

## Supported waste types

| PDF content | Type returned |
|-------------|---------------|
| Vegyes hulladékgyűjtési nap (weekday / seasonal weekday rules) | Communal |
| szelektív (date table) | Selective |
| zöldhulladék (date table) | Green |
| Lomtalanítás date(s) | Bulky |

## Notes

- Mixed (`Communal`) collection is written as free text, often with seasonal ranges such as `01.01-03.31 és 10.01-12.31 között CSÜTÖRTÖK` and a different weekday in summer. The source expands those rules for the calendar year.
- Bulky waste (`Lomtalanítás`) is a single date on many settlement PDFs. Some towns list several optional dates on page 2 (`Lomtalanítási időpontok`); all of those dates are returned. Siófok PDFs only describe bulky collection by week and neighbourhood without a calendar day, so no Bulky entries are produced there.
- `Zamárdi Kőhegy` is currently published as a PowerPoint file (`.pptx`) rather than a PDF, so that area cannot be parsed until Siókom publishes a PDF.
- The PDF is a PowerPoint export; the parser uses `pypdf` layout extraction to keep month columns aligned.

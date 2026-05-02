# Rybnik

Support for schedules provided by [Miasto Rybnik / EKO Sp. z o.o.](https://www.rybnik.eu), serving Rybnik, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rybnik_pl
      args:
        district: DISTRICT_NAME
        sub_district: REJON_NAME
        property_type: residential
```

### Configuration Variables

**`district`** *(string) (required)*

The district / area group name, which determines which PDF schedule file is downloaded.
Must be one of the values in the [District Names](#district-names) table below.

**`sub_district`** *(string) (optional)*

The Rejon (zone) name as it appears in the leftmost column of the PDF schedule table
(e.g. `Paruszowiec-Piaski`, `Kamień 1`, `Kamień 2`).
When omitted, entries for **all** Rejony within the district PDF are returned.

**`property_type`** *(string) (optional, default: `residential`)*

| Value | Description |
|---|---|
| `residential` | Single-family homes (nieruchomości zamieszkałe) |
| `commercial` | Commercial / business premises (nieruchomości niezamieszkałe / firmy) |

## District Names

Use one of these exact strings for the `district` argument:

| District name |
|---|
| `Boguszowice Stare` |
| `Chwalowice / Boguszowice Os. / Klokocin` |
| `Gotartowice` |
| `Grabownia / Golejow / Ochojec` |
| `Ligota` |
| `Maroko-Nowiny` |
| `Niedobczyce` |
| `Niewiadom` |
| `Orzepowice / Stodoly / Chwalecice` |
| `Paruszowiec / Kamien` |
| `Polnoc` |
| `Radziejow / Popielow` |
| `Smolna / Zamyslow / Meksyk` |
| `Srodmiescie / Wielopole / Kuznia` |
| `Zebrzydowice` |

## Examples

### Residential — specific Rejon

```yaml
waste_collection_schedule:
  sources:
    - name: rybnik_pl
      args:
        district: "Paruszowiec / Kamien"
        sub_district: "Paruszowiec-Piaski"
```

### Residential — all Rejony in a district

```yaml
waste_collection_schedule:
  sources:
    - name: rybnik_pl
      args:
        district: "Boguszowice Stare"
```

### Commercial

```yaml
waste_collection_schedule:
  sources:
    - name: rybnik_pl
      args:
        district: "Niedobczyce"
        property_type: commercial
```

## How to get the source arguments

1. Go to the [Rybnik waste collection schedules page](https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne/) and navigate to the current year's schedules.
2. Download the PDF for the district that covers your address.
3. Open page 2 of the PDF — the schedule table lists Rejon (zone) names in the leftmost column.
4. Use the district name from the [District Names](#district-names) table and the exact Rejon name from the PDF as your `district` and `sub_district` arguments.

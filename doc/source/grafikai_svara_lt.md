# Kauno švara

Support for schedules provided by [UAB "Kauno švara"](https://www.svara.lt), the waste collection company for Kaunas city and district, Prienai, Birštonas, Alytus (city and district), Druskininkai, Kaišiadorys and parts of Vilnius (Lithuania).

The source reads the company's **open-data CSV export** (SharePoint "Atviri duomenys" site, refreshed every night around 03:00). The interactive search at [grafikai.svara.lt](https://grafikai.svara.lt) is protected by a Cloudflare Turnstile browser check and cannot be used by integrations any more; the open-data export is the official machine-readable alternative.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: REGION
        street: STREET_NAME
        house_number: HOUSE_NUMBER
        district: DISTRICT          # optional
        city: CITY                  # optional
        containers:                 # optional
          - CONTAINER_ID
```

### Configuration Variables

**region**
*(string) (required)*

Municipality as used by Kauno švara, e.g. `Kauno m. sav.`, `Kauno r. sav.`, `Prienų r. sav.`, `Alytaus m. sav.`, `Alytaus r. sav.`, `Druskininkų sav.`, `Birštono sav.`, `Kaišiadorių r. sav.`, `Vilniaus m. sav.`.

**street**
*(string) (required)*

Street name including the abbreviation, e.g. `Demokratų g.`.

**house_number**
*(string) (required)*

House number as registered, e.g. `7`, `2A`, `132B`. Letter case does not matter.

**district**
*(string) (optional)*

Seniūnija, e.g. `Išlaužo sen.`. Only needed when the same street and house number exists in several districts of the region. The source lists the possible values if the address is ambiguous.

**city**
*(string) (optional)*

City or settlement, e.g. `Kauno m.`, `Garliavos m.`, `Domeikavos k.`. Alternative to `district` for disambiguation.

**containers**
*(list of string) (optional)*

Container IDs (e.g. `MK-004108`) to restrict the result to specific containers of the address. If omitted, all containers registered at the address are returned.

**waste_object_ids**
*(deprecated)*

Numeric IDs of the former grafikai.svara.lt API are no longer available and this argument is ignored. Use `containers` instead.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: Kauno m. sav.
        street: Demokratų g.
        house_number: 7
```

Address that exists in two districts of the same region:

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: Prienų r. sav.
        district: Išlaužo sen.
        street: Alytaus g.
        house_number: 2
```

## How to get the source arguments

Use the same values as in the address search on [grafikai.svara.lt](https://grafikai.svara.lt):

| Page field            | YAML argument |
|-----------------------|---------------|
| Regionas              | region        |
| Seniūnija             | district      |
| Gatvė                 | street        |
| Namo numeris          | house_number  |

If a value is misspelled, the source raises an error listing the valid regions, the closest matching streets, or the house numbers known on that street.

## Notes

- The open data contains only the *next* collection date(s) per container together with a textual frequency (`kas 14 dienų`, `antrąjį mėnesyje antradienį`, ...). The source extrapolates further dates from that frequency for about two months ahead. The official next date is refreshed daily, so any deviation (for example a holiday shift) corrects itself as the date approaches.
- Waste type names are taken verbatim from the open data: `Mišrios komunalinės`, `Antrinės žaliavos (popierius/plastikas)`, `Antrinės žaliavos (pakuotės)`, `Antrinės žaliavos (stiklas)`, `Maistinės atliekos`, `Žaliosios atliekos`, `Stambiagabaritės`. Use `customize` to rename them.
- The CSV is about 55 MB and is downloaded at most once every 6 hours per Home Assistant instance, shared between all configured addresses.

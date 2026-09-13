# Gemeinde Maur

This source provides waste collection dates for the municipality of **Maur** in the Canton of Zurich, Switzerland.

## Configuration

This source does not require any configuration parameters. All waste collection dates apply to the entire municipality.

```yaml
waste_collection_schedule:
  sources:
    - name: maur_ch
      args: {}
```

## Waste Types

The following waste types are supported:

| Type | Icon | Description |
|------|------|-------------|
| Grüngut | 🌱 | Organic waste (garden and kitchen) |
| Grüngut/Christbaum | 🌱 | Organic waste incl. Christmas trees |
| Kehricht | 🗑️ | General waste / household trash |
| Karton | 📦 | Cardboard |
| Papiersammlung | 📦 | Paper collection |
| Metall | ♻️ | Metal |
| Sonderabfall | ⚗️ | Special/hazardous waste |
| Häcksel-Service / Häckseldienst | ✂️ | Chipping service |
| Hauptsammelstelle | ♻️ | Main collection point |

The provider appends dates and district names to the `Häcksel-Service` and
`Hauptsammelstelle` event titles. These are normalized back to the two canonical
names above so that the waste types stay stable from year to year.

## Data Source

The data is scraped from the official municipality website:
- **Website**: https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html
- **Waste Management Contact**: abfall@maur.ch / +41 43 366 13 90

The event list on that page is paginated; the source follows the pagination so that
the full published schedule is returned, not just the first page of upcoming dates.

## Notes

- All collection dates apply to the whole municipality area (Maur, Ebmatingen, Binz, Uessikon, Forch)
- Collection times are typically from 6:45 AM onwards, unless specified otherwise
- For special waste (Sonderabfall), specific time windows apply (usually 8:00-11:30 AM)

## Owner

This source is currently unclaimed. If you are a maintainer or frequent contributor to this source, please add your GitHub handle to the `SOURCE_CODEOWNERS` list in the source file.

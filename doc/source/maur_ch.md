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
| Kehricht | 🗑️ | General waste / household trash |
| Karton | 📦 | Cardboard |
| Sonderabfall | ⚗️ | Special/hazardous waste |
| Häcksel-Service / Häcksel Dienst | ✂️ | Chipping service |
| Hauptsammelstelle | ♻️ | Main collection point |

## Data Source

The data is scraped from the official municipality website:
- **Website**: https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html
- **Waste Management Contact**: abfall@maur.ch / +41 43 366 13 90

The waste collection schedule is published for the current year and includes all collection dates for the entire municipality of Maur.

## Notes

- All collection dates apply to the whole municipality area (Maur, Ebmatingen, Binz, Uessikon, Forch)
- Collection times are typically from 6:45 AM onwards, unless specified otherwise
- For special waste (Sonderabfall), specific time windows apply (usually 8:00-11:30 AM)

## Owner

This source is currently unclaimed. If you are a maintainer or frequent contributor to this source, please add your GitHub handle to the `SOURCE_CODEOWNERS` list in the source file.

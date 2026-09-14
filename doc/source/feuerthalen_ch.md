# Gemeinde Feuerthalen

This source provides waste collection dates for the municipality of **Feuerthalen** in the Canton of Zurich, Switzerland.

## Configuration

This source does not require any configuration parameters. All waste collection dates apply to the entire municipality.

```yaml
waste_collection_schedule:
  sources:
    - name: feuerthalen_ch
      args: {}
```

## Waste Types

The following waste types are supported:

| Type | Icon | Description |
|------|------|-------------|
| Hauskehricht | 🗑️ | General household waste, collected every Monday |
| Grüngut | 🌱 | Organic garden and kitchen waste |
| Direktentsorgung Werkhof | ♻️ | Monthly drop-off day at the Werkhof depot |
| Altpapier/Karton | 📦 | Paper and cardboard |
| Sonderabfälle/Giftsammlung | ⚗️ | Annual household hazardous-waste collection |

## Data Source

The data is scraped from the municipality's official waste calendar (Abfallkalender), a PDF
published each year on the online counter:
- **Website**: https://www.feuerthalen.ch/umwelt/entsorgung/abfall.html/275
- **Calendar page**: https://www.feuerthalen.ch/verwaltung/online-schalter.html/384/product/7

Grüngut, Werkhof, Altpapier/Karton and Sonderabfälle dates are read from the coloured day cells
of the calendar grid. Hauskehricht is collected every Monday; the two yearly holiday-shift
exceptions (e.g. Easter Monday / Whit Monday moved to the following Wednesday) are parsed from
the calendar's own exception notes, so no dates are hardcoded.

## Notes

- All collection dates apply to the whole municipality of Feuerthalen.
- The published PDF changes every year; this source always fetches the current one.

## Owner

[@oh-supra](https://github.com/oh-supra)

# Gruppo Veritas

Support for schedules provided by [Gruppo Veritas](https://www.gruppoveritas.it/), a waste collection operator covering several municipalities in the Venice metropolitan area (Italy), including Jesolo.

Waste collection data is published exclusively as downloadable PDF calendars. This source downloads the PDF and extracts the schedule using `pypdf`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gruppo_veritas_it
      args:
        pdf_url: https://www.gruppoveritas.it/sites/default/files/documenti/calendari/jesolo_calendario_raccolta_differenziata_2026.pdf
        year: 2026
```

### Configuration Variables

**pdf_url**  
*(string) (required)*  
Direct URL to the PDF calendar. Find it on the Gruppo Veritas website under your municipality's waste collection page. The URL changes each year when a new calendar is published.

**year**  
*(integer) (optional, default: `2026`)*  
The calendar year to extract. Must match the year printed inside the PDF. Update this value (together with `pdf_url`) when the new annual calendar is published.

## How to find the PDF URL

1. Go to [https://www.gruppoveritas.it](https://www.gruppoveritas.it)
2. Navigate to your municipality's page (e.g. Jesolo → Rifiuti → Calendario raccolta)
3. Right-click the PDF download link and copy the link address
4. Paste it into the `pdf_url` field

## Supported waste types

| Badge | Waste type |
|-------|------------|
| C | Carta/Cartone (paper and cardboard) |
| VPL | Vetro/Plastica/Lattine (glass, plastic, cans) |
| S | Secco (residual dry waste) |
| UO | Umido/Organico (organic/food waste) |
| VR | Verde/Ramaglie (garden waste) |

## Notes

- The calendar PDF contains two months per page in a side-by-side layout. The parser uses `pypdf` with `extraction_mode="layout"` to reliably separate the two columns.
- Suspended collections (`RACCOLTA SOSPESA`) are correctly omitted from the schedule.
- Postponed collections (`POSTICIPATA AL DD/MM`) are moved to the indicated date.
- Due to a font encoding artefact in the PDF, a VR (Verde/Ramaglie) badge that appears inline as part of a postponement note may be extracted as VPL. This affects only the rare case of a postponed Verde/Ramaglie pickup and cannot be corrected in the parser.
- The PDF may include a partial preview of January of the following year; only events for the configured `year` are returned.
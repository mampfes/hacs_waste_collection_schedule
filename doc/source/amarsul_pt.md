# Amarsul

Support for waste collection schedules provided by [Amarsul](https://www.amarsul.pt), Portugal.

Amarsul publishes its selective-collection calendars as single-page PDF files whose page is one embedded image. This source downloads the PDF, extracts the embedded image, and reads the yearly grid by detecting the colour-filled day cells (blue = paper/cardboard, yellow = lightweight packaging). The year is read from the PDF link, so the schedule is parsed live rather than hardcoded.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: amarsul_pt
      args:
        calendar_url: CALENDAR_PDF_URL
```

### Configuration Variables

**calendar_url**
*(string) (required)*

Direct link to the Amarsul collection-calendar PDF for your circuit. Each circuit (e.g. D230A, D249A, ...) has its own calendar PDF.

## How to find your `calendar_url`

1. Go to [https://www.amarsul.pt](https://www.amarsul.pt) and open the collection-calendar page for your municipality / circuit.
2. Open the calendar PDF for your circuit.
3. Copy the direct link to the PDF file (it ends in `.pdf`).
4. Use that link as the `calendar_url` argument.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: amarsul_pt
      args:
        calendar_url: "https://www.amarsul.pt/media/orllbvsf/calend%C3%A1rio-recolhas-2026-d230a-d231a-d249a-d250a-d251a-d252a-d253a-e-d254a.pdf"
```

## Bin types returned

| Provider description (legend) | Returned type   | Icon                    |
|-------------------------------|-----------------|-------------------------|
| Contentor Papel/Cartão (blue) | `Papel/Cartão`  | `Icons.PAPER`           |
| Contentor Embalagens (yellow) | `Embalagens`    | `Icons.PLASTIC_PACKAGING` |

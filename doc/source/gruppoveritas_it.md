# Gruppo Veritas

Support for schedules provided by [Gruppo Veritas](https://www.gruppoveritas.it/).

Waste collection schedules published as PDF calendars by Gruppo Veritas (Jesolo and other municipalities).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gruppoveritas_it
      args:
        pdf_url: PDF_URL
        year: YEAR
```

### Configuration Variables

**pdf_url**  
*(string) (optional)*

**year**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gruppoveritas_it
      args:
        pdf_url: https://www.gruppoveritas.it/sites/default/files/documenti/calendari/jesolo_calendario_raccolta_differenziata_2026.pdf
        year: 2026
```

## How to get the source arguments

Open https://www.gruppoveritas.it, navigate to your municipality's waste collection page, locate the PDF calendar download link, and paste its URL into the pdf_url field.

# Amarsul

Support for schedules provided by [Amarsul](https://www.amarsul.pt).

Source for Amarsul selective-collection calendars, Portugal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: amarsul_pt
      args:
        calendar_url: CALENDAR_URL
```

### Configuration Variables

**calendar_url**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: amarsul_pt
      args:
        calendar_url: https://www.amarsul.pt/media/orllbvsf/calend%C3%A1rio-recolhas-2026-d230a-d231a-d249a-d250a-d251a-d252a-d253a-e-d254a.pdf
```

## How to get the source arguments

Find the collection calendar (PDF) for your circuit on the Amarsul website (https://www.amarsul.pt) and copy the direct link to the PDF file. Each circuit has its own calendar PDF.

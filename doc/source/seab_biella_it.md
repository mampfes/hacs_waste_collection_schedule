# SEAB Biella

Support for schedules provided by [SEAB Biella](https://www.seab.biella.it/) (Società Ecologica Area Biellese), in Italy.

## Configuration via Home Assistant

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `url` | string | The URL to the PDF calendar file. |

### How to get the URL
1. Visit the [SEAB Biella - Aree Servite](https://www.seab.biella.it/aree-servite) page.
2. Select your municipality.
3. Locate the "Eco-calendario" or "Calendario Raccolta Rifiuti" link (usually a PDF for the current year or semester).
4. Copy the link address (URL) and use it in the configuration.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: seab_biella_it
      args:
        url: https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf
```

## Returned collection types
- Indifferenziato
- Organico
- Carta
- Plastica
- Vetro (if present in the calendar)
- Sfalci (if present in the calendar)

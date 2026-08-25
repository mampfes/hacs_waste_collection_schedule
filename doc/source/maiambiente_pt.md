# Maiambiente

Support for schedules provided by [Maiambiente](https://www.maiambiente.pt), the
municipal waste operator of Maia, Portugal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maiambiente_pt
      args:
        rua: STREET
        numero: HOUSE_NUMBER
```

### Configuration Variables

**rua**  
*(string) (required)*

**numero**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maiambiente_pt
      args:
        rua: "Rua Sol (Milheirós)"
        numero: "20"
```

## How to get the source arguments

Search for your street at <https://servicos.maiambiente.pt/cal2026/> and use the
exact street name shown in the suggestion list — it includes the parish in
brackets, e.g. `Rua Sol (Milheirós)`. Then pick your house number and use it
exactly as listed.

Two things catch people out:

- The street search ignores Portuguese prepositions. Searching for
  `Monte das Cruzes` returns nothing; `Monte Cruzes` returns
  `Rua Monte Cruzes (Milheirós)`.
- House numbers are not always plain numbers. Some are compound (`76, 1`,
  `118, Rc`) and some are building names (`Biblioteca da Maia`). Use whatever
  the list shows, verbatim.

## Supported waste types

| Type | Stream |
|---|---|
| **Resíduos indiferenciados** | Mixed/undifferentiated waste |
| **Papel e cartão** | Paper and cardboard |
| **Embalagens de plástico e metal** | Plastic and metal packaging |
| **Vidro** | Glass |
| **Resíduos alimentares** | Food waste |
| **Resíduos de jardim** | Garden waste |
| **Não haverá recolha** | Marks a suspended collection (holidays) |

Which of these appear depends on the circuit: central Maia circuits typically
have no food or garden waste collection at all.

## Notes

- No login is required.
- Maiambiente publishes the calendar as a PDF whose body is a bitmap. The
  source reads it *geometrically* — the month block, weekday row and week
  column give the date, the fill colour gives the waste stream — so no OCR is
  involved and no OCR dependency is added. The decoding needs `Pillow`, which
  Home Assistant Core already ships as a base requirement.
- The calendar belongs to the collection *circuit*, not to the address, and it
  covers a whole year, so it is fetched once per year and cached.
- Every Maiambiente path carries the year (`cal2026/cal2026.php`,
  `type=arruamento2026`, …), so the address is re-resolved for each year: one
  year's internal id is not necessarily valid in the next. Once the current
  calendar nears its end, the next year's is picked up automatically, which
  covers the December-to-January transition.
- A single day can carry two streams (holiday compensation) — both are
  returned.
- The server rejects bursts of requests with HTTP 403, so requests are spaced
  out by 1.5 s.
- Collections start at 14:00 local time.
- Maiambiente's servers send an **incomplete TLS certificate chain** (the
  intermediate is missing, so browsers recover via AIA fetching but Python does
  not). The service module supplies that intermediate itself; certificate
  verification stays fully enabled.

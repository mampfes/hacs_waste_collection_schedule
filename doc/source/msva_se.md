# Mittsverige Vatten & Avfall

Support for schedules provided by [Mittsverige Vatten & Avfall (MSVA)](https://www.msva.se/) for addresses in Sundsvall kommun, Sweden. Data is fetched from the open API hosted at `api.sundsvall.se` (municipality code `2281`). Addresses in Timrå and Nordanstig are not supported by this API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: msva_se
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        postal_code: POSTAL_CODE
        city: CITY
        additional_information: ADDITIONAL_INFORMATION
```

### Configuration Variables

**street**
*(String) (required)* — Street name without house number, e.g. `Västra Radiogatan`.

**house_number**
*(String) (required)* — House number, e.g. `18`.

**postal_code**
*(String) (required)* — 5-digit Swedish postal code, e.g. `85461`.

**city**
*(String) (optional, default: `Sundsvall`)* — Locality within Sundsvall kommun.

**additional_information**
*(String) (optional)* — House letter or unit identifier, e.g. `A`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: msva_se
      args:
        street: Västra Radiogatan
        house_number: 18
        postal_code: 85461
        city: Sundsvall
```

## How to get the source arguments

Use the same address you would enter on the MSVA site at <https://www.msva.se/>. The API is documented at <https://api.sundsvall.se/Garbage/api-docs>.

## Notes

The API returns only the next pickup day, which covers two waste types: food waste (matavfall, collected every pickup) plus one rotating type — residual (restavfall), paper (pappersförpackningar) or plastic (plastförpackningar) — on a 6-week cycle. Home Assistant refreshes the source periodically, so the next pair appears after each pickup.

# STKH Sopron és Térsége Nonprofit Kft.

Support for waste collection schedules provided by [STKH Sopron és Térsége Nonprofit Kft.](https://stkh.hu), the public waste management service of Sopron and its surroundings (Győr-Moson-Sopron and Vas counties), Hungary.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
      - name: stkh_hu
        args:
          municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**
*(string) (required)*

Name of the settlement as listed in the waste calendar on <https://stkh.hu>.

## Example

```yaml
waste_collection_schedule:
    sources:
      - name: stkh_hu
        args:
          municipality: "Újkér"
```

## How to get the source arguments

1. Open <https://stkh.hu>.
2. Scroll to the waste calendar (`Hulladéknaptár`) list of settlements on the home page.
3. Find your settlement and use its name as the `municipality` argument, for example `Újkér`.

Accents, capitalisation, spaces and hyphens are ignored when matching, so `ujker` resolves to `Újkér` as well. If the name cannot be found, the integration raises an error listing all supported settlements.

## Bin types returned

| Provider description | Returned type | Icon |
|---------------------|--------------|-----------------------|
| `vegyes hulladék` (mixed/residual waste) | `Vegyes` | `Icons.GENERAL_WASTE` |
| `szelektív` (paper, plastic and metal packaging) | `Szelektív` | `Icons.RECYCLING` |
| `zöldhulladék` (garden waste, Christmas trees in January and February) | `Zöldhulladék` | `Icons.GARDEN` |

## Notes and limitations

- STKH publishes each settlement's calendar as a one-page PDF and re-issues it for the second half of the year. This source downloads every edition linked from the home page and, where two editions overlap, uses the newer one — collection days do occasionally change mid-year.
- Mixed waste is published only as a weekday (`Vegyes hulladékgyűjtési nap: kedd`) rather than as a list of dates, so the weekly occurrences are generated from that weekday. A few settlements state `körzetbeosztás szerint` ("by district") instead; for those, no mixed waste collections are returned.
- Public holiday shifts to the mixed waste schedule are **not** reflected, because STKH does not publish them in a machine-readable form. Check <https://stkh.hu> around public holidays.
- The larger towns (Sopron, Kapuvár, Körmend, Kőszeg, Csepreg, Sárvár, Celldömölk, Bük, Szentgotthárd, Fertőszentmiklós) publish per-street PDFs in a different layout. Those are **not** supported yet.

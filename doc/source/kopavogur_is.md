# Kópavogsbær

Support for schedules provided by [Kópavogur municipality](https://www.kopavogur.is), Iceland. Collection is operated by Kubbur.

The schedule is published as two color-coded PDF calendars per year (one for general/food waste, one for paper/plastic). This source downloads the PDFs and decodes the highlighted calendar cells for the selected collection district.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kopavogur_is
      args:
        district: DISTRICT
```

### Configuration Variables

**district** *(string) (required)*: The collection district (zone) as shown in the legend of the official calendar. Partial, case-insensitive matches are accepted (e.g. `Lindir`).

Valid districts:

- `Vesturbær - Smárahverfi` (yellow)
- `Austurbær sunnan Álfhólsvegar` (purple)
- `Austurbær norðan Álfhólsvegar` (red)
- `Lindir, Salir, Kórar, Hvörf og Þing` (blue)

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kopavogur_is
      args:
        district: "Lindir, Salir, Kórar, Hvörf og Þing"
```

## Notes

The `Lindir, Salir, Kórar, Hvörf og Þing` district is collected over two consecutive days; both days are reported.

The official calendar states that dates are indicative: weather, illness, breakdowns and other unforeseen factors may shift collection by 1–2 days between neighborhoods.

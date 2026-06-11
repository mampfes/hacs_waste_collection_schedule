# Heimat-Info

Support for waste collection schedules provided by [Heimat-Info](https://www.heimat-info.de), a platform used by multiple German municipalities.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: heimat_info_de
      args:
        commune: COMMUNE_SLUG
        area: AREA_NAME
```

### Configuration Variables

**commune**
*(String) (required)*

The URL slug of your commune on heimat-info.de. You can find it in the URL:
`https://www.heimat-info.de/gemeinden/<slug>/abfallkalender`

For example, Gründau uses the slug `gruendau`.

**area**
*(String) (optional)*

The name of the collection area / district (e.g. `Breitenborn`). Can be omitted if the commune has only one area. If the commune has multiple areas and no area is specified, the source will raise an error listing the available area names.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: heimat_info_de
      args:
        commune: gruendau
        area: Breitenborn
```

## How to get the source arguments

1. Open [https://www.heimat-info.de](https://www.heimat-info.de) and search for your commune.
2. Navigate to the **Abfallkalender** section.
3. The commune **slug** is the part of the URL after `/gemeinden/`, e.g. for `https://www.heimat-info.de/gemeinden/gruendau/abfallkalender` the slug is `gruendau`.
4. If the calendar page lists multiple collection areas (Abholbereiche), click on yours. The area **name** appears in the list, e.g. `Breitenborn` or `Gettenbach`.
5. If there is only one area, you can omit the `area` parameter.

# WasteNet Southland

Support for schedules provided by [Auckland Council](https://aucklandcouncil.govt.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aucklandcouncil_govt_nz
      args:
        area_number: AREA_NUMBER_FROM_COLLECTION_PAGE # see 'How to get the source argument below'
```

### Configuration Variables

**area_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aucklandcouncil_govt_nz
      args:
        area_number: 12342306525
```

## How to get the source argument

The source argument is the area number from Auckland Council site:

-  Open your collection days page by  entering your address [on the Auckland Council collection day finder](https://www.aucklandcouncil.govt.nz/rubbish-recycling/rubbish-recycling-collections/Pages/rubbish-recycling-collection-days.aspx)
- Look for 'an' parameter in your browser URL, e.g. https://www.aucklandcouncil.govt.nz/rubbish-recycling/rubbish-recycling-collections/Pages/collection-day-detail.aspx?an=12342306525
- In this example the area number is `12342306525`.

# Aberdeen City Council (integration.aberdeencity.gov.uk)

This source fetches bin collection dates for properties in the City of Aberdeen, Scotland, via the council's public Granicus Firmstep "Self" bin-collection-calendar form (`integration.aberdeencity.gov.uk/service/bin_collection_calendar___view`).

This is the **city** of Aberdeen council. The surrounding shire is covered separately by [`aberdeenshire_gov_uk`](aberdeenshire_gov_uk.md).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aberdeencity_gov_uk
      args:
        uprn: YOUR_UPRN
```

### Configuration Variables

- **uprn** _(string) (required)_: Unique Property Reference Number for your property.

### Example

```yaml
waste_collection_schedule:
  sources:
    - name: aberdeencity_gov_uk
      args:
        uprn: "9051064786"
```

## How to find your UPRN

Use [Find My Address](https://www.findmyaddress.co.uk/) or check your council tax bill / waste-collection notice. Aberdeen UPRNs typically begin with `9051…`.

## Returned Waste Types

The source returns whichever streams the council reports for the property. Common ones include:

- General Waste
- Mixed Recycling
- Food and Garden Waste
- Food Waste

Each entry includes the collection date and the waste-type label.

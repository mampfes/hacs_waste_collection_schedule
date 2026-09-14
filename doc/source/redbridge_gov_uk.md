# Redbridge Council

Support for schedules provided by [Redbridge Council](https://www.redbridge.gov.uk/), serving Redbridge, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: redbridge_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


## Collection Types

The source returns one collection per service printed on the Redbridge calendar PDF:

| Type | Icon |
|-|-|
| `Refuse` | `mdi:trash-can` |
| `Recycling` | `mdi:recycle` |
| `Food` | `mdi:food-apple` |
| `Garden` | `mdi:flower` |

Redbridge added the weekly food waste collection to household rounds, so `Food`
appears in the calendar of an eligible property. A property keeps only the types
that Redbridge collects from it, so a calendar does not always contain all four.

Use these names in the `types` option of a sensor. The names are the labels used
by the PDF, so the garden waste type is `Garden` and not `Garden Waste`.

## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: redbridge_gov_uk
      args:
        uprn: 10034922090
```


#### How to find your `UPRN`
Your uprn is the collection of numbers at the end of the url when downloading a collection calendar for your collection schedule on the Redbridge web site.

For example:  _https://my.redbridge.gov.uk/RecycleRefuse/GetFile?uprn=10034922090_

Alternatively, you can discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.




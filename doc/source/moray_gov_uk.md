# Moray Council

Support for schedules provided by [Moray Council](https://www.moray.gov.uk/), serving Moray, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
  - name: moray_gov_uk
    args:
      id: UNIQUE_PROPERTY_ID
```

### Configuration Variables

**id**<br>
*(string) (required)*


#### How to find your `id`
Your `id` is the collection of numbers at the end of the url when looking up your collection schedule on the [Moray Council Bin Day Finder](https://bindayfinder.moray.gov.uk/) web site.

For example:  _https://bindayfinder.moray.gov.uk/disp_bins.php?id=`00027199`_


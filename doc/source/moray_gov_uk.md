# Moray Council

Support for schedules provided by [Moray Council](https://www.moray.gov.uk/), serving Moray, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: moray_gov_uk
      args:
        bin_id: UNIQUE_PROPERTY_BIN_ID
```

### Configuration Variables

**bin_id**<br>
*(string) (required)*


## Example
```yaml
waste_collection_schedule:
    sources:
    - name: moray_gov_uk
      args:
        bin_id: "01234567"
```


#### How to find your `bin_id`
Your `bin_id` is the collection of numbers at the end of the url when looking up your collection schedule on the [Moray Council Bin Day Finder](https://bindayfinder.moray.gov.uk/) web site.

For example:  _https://bindayfinder.moray.gov.uk/disp_bins.php?id=`00027199`_


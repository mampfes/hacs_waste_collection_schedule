# Stockport Metropolitan Borough Council

Support for schedules provided by [Stockport Metropolitan Borough
Council](https://www.manchester.gov.uk/bincollections/), serving the
area of Stockport, UK.

With thanks to the creator of the schedule for Manchester, UK, from
whom some of the code is re-factored.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stockport_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stockport_gov_uk
      args:
        uprn: "10090543805"
```

## How to get the source argument

The UPRN code can be found in the page by entering your postcode on the
[Stockport Bin Collections page
](https://www.stockport.gov.uk/find-your-collection-day/).

Select your house from the drop-down, then the UPRN is the final part of
the URL that you are re-directed to.

For example, for post-code SK6 3AA, house number 25, you are re-directed to


https://myaccount.stockport.gov.uk/bin-collections/show/10090543805

The UPRN is 10090543805

# North Adelaide Waste Management Authority (South Australia)

Support for schedules provided by [North Adelaide Waste Management Authority](https://www.nawma.sa.gov.au/kerbside-collections/bin-collection-days/).
This covers Salisbury, Playford, and Gawler councils.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nawma_sa_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**street_number**<br>
*(string) (optional)*

Only required if the street crosses multiple collection areas with different days.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nawma_sa_gov_au
      args:
        suburb: Whites Road
        street_name: Paralowie
```

## How to get the source arguments

Visit the [North Adelaide Waste Management Authority collection days](https://www.nawma.sa.gov.au/kerbside-collections/bin-collection-days/) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and (if required) the number portion of the auto-completed address.

Note: Some addresses can be quite obscure, for example for the Gawler main street set `street_name` to `'Murray Street (sec between Ayers and the railway line'`.

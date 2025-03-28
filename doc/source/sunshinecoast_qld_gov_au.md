# Sunshine Coast QLD

Support for schedules provided by [Sunshine Coast Council](https://www.sunshinecoast.qld.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: STREET NAME
```

### Configuration Variables

**street_name**  
*(string) (required)*


## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: Great Keppel Way
```

## How to get the source arguments
Visit the [Sunshine Coast Council Bin Collection Calendar](https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days) page and look type in your street name. Similar street names should pop up and this wil update the calendar below. Sunshine Coast Council site performs an an [API](https://www.sunshinecoast.qld.gov.au/__server__/api/v1/streets/STREET_NAME) which returns a json formatted response. The response is the id of the street, the street name, the suburb, the day of the week collection occurs, and a week number (either 1 or 2). The week number is a corresponding week starting from the 11 December 2023.

If the week number for your street is 1, this means your `Recycling` is collected every second week starting from the originated base date (11/12/23). If your week number is 2, this means your `Recycling` is collected the week after the base week and ever second week thereafter. For the weeks that it isn't the streets collection week, the `Organic` bin is collected, and each and every week the `General Garbage` bin is collected.

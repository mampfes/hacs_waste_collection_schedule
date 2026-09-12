# Sunshine Coast QLD

Support for schedules provided by [Sunshine Coast Council](https://www.sunshinecoast.qld.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: STREET NAME
        locality: SUBURB
```

### Configuration Variables

**street_name**  
*(string) (required)*

The street name as the council's bin collection page spells it, e.g. `Hospital Rd`. A house number and suburb are ignored if you include them, so `12 Hospital Rd, Nambour` also works.

**locality**  
*(string) (optional)*

The suburb. Only needed when the same street name occurs in more than one suburb — `Main St`, for example, exists in five. Without it, the configuration fails with an error listing the matching streets and their suburbs, rather than picking one of them.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: Great Keppel Way
```

```yaml
waste_collection_schedule:
  sources:
    - name: sunshinecoast_qld_gov_au
      args:
        street_name: Main St
        locality: Eumundi
```

## How to get the source arguments

Visit the [Sunshine Coast Council Bin Collection Calendar](https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days) page and type in your street name. Similar street names pop up and update the calendar below. The council's site queries an [API](https://www.sunshinecoast.qld.gov.au/__server__/api/v1/streets/STREET_NAME) which returns a json formatted response: the id of the street, the street name, the suburb, the day of the week collection occurs, and a week number (either 1 or 2).

The API searches its own street names for a substring, and it abbreviates the street type (`Rd`, `St`, `Bvd`, `Ct`). A spelled-out type such as `Hospital Road` matches nothing on its own, so this source retries with the abbreviation and then without the type at all.

If the week number for your street is 1, this means your `Recycling` is collected every second week starting from the base date the source counts from (11 December 2021). If your week number is 2, this means your `Recycling` is collected the week after the base week and every second week thereafter. For the weeks that it isn't the street's collection week, the `Organic` bin is collected, and each and every week the `General Garbage` bin is collected.

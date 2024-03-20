# Port Stephens Council

Support for schedules provided by [Port Stephens Council Waste and Recycling](https://www.portstephens.nsw.gov.au/services/waste-and-recycling/household-rubbish-and-recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: portstephens_nsw_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: portstephens_nsw_gov_au
      args:
        suburb: Campvale
        street_name: Richardson Road
        street_number: 969
```

## How to get the source arguments

Visit the [Port Stephens Council Waste and Recycling](https://apps.impactapps.com.au/port-stephens/calendar/) page and search for your address. The arguments should exactly match the results shown for Suburb, Street and number portion of the Property.

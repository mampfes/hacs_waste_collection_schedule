# Croydon Council

Support for schedules provided by [Croydon Council](https://www.croydon.gov.uk/), serving Croydon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: croydon_gov_uk
      args:
        postcode: POSTCODE
        houseID: HOUSE_NUMBER & STREET
```

### Configuration Variables

**postcode**
*(string) (required)*

**houseID**
*(string) (required)*

houseID should be in the format used by the website, road names tend not to be abbreviated.


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: croydon_gov_uk
      args:
        postcode: "CR0 2EG"
        houseID: "23B Howard Road"
```

Note: Croydon website stops responding if repeated queries are made in quick succession. This shouldn't be an issue in normal use where HA is querying once per day, but repeated HA restarts may result in schedules not being returned. 
# Inverclyde Council

Support for schedules provided by [Inverclyde Council](https://www.inverclyde.gov.uk), serving Inverclyde, Scotland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: inverclyde_gov_uk
      args:
        postcode: "PA16 0FG"
        address: "1 Findhorn Crescent"
```

### Configuration Variables

**postcode**
*(String) (required)*

The postcode of the property, e.g. `PA16 0FG`.

**address**
*(String) (required)*

The first line of the address exactly as returned by the council's address search, e.g. `10 St John's Road`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: inverclyde_gov_uk
      args:
        postcode: "PA16 0FG"
        address: "1 Findhorn Crescent"
```

## How to get the source argument

Visit <https://maps.inverclyde.gov.uk/noticeboard8/noticeboard.aspx>, search for your postcode and note down your address exactly as it is shown in the address list, e.g. `10 St John's Road`. If the address you provide is not found, the error message will list the exact address strings the council's system knows about for that postcode so you can pick the correct one.

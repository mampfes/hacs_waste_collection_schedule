# Derbyshire Dales District Council

Support for schedules provided by [Derbyshire Dales District Council](https://www.derbyshiredales.gov.uk/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: derbyshiredales_gov_uk
      args:
        address_id: <uprn> or <postcode>
```

### Configuration Variables

**address_id**
*(string) (required)*

Your Unique Property Reference Number (UPRN) or postcode. A UPRN works best.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: derbyshiredales_gov_uk
      args:
        address_id: U10070089522
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

# Clackmannanshire Council

Support for schedules provided by [Clackmannanshire Council](https://www.clacks.gov.uk/), serving Clackmannanshire, Scotland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: clackmannanshire_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**
*(String) (required)*

Your postcode, e.g. `FK10 3EY`.

**address**
*(String) (required)*

Your address, exactly as shown in the search results on the council website, e.g. `16 Crophill, Sauchie`. Commas are optional and will be ignored.

**garden_waste**
*(Boolean) (optional, default: `false`)*

Set to `true` if you hold a paid garden waste (brown bin) permit, to also include its collection dates.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: clackmannanshire_gov_uk
      args:
        postcode: "FK10 3EY"
        address: "16 Crophill, Sauchie"
```

```yaml
waste_collection_schedule:
    sources:
    - name: clackmannanshire_gov_uk
      args:
        postcode: "FK10 3EY"
        address: "16 Crophill, Sauchie"
        garden_waste: true
```

## How to get the source arguments

Go to [https://www.clacks.gov.uk/environment/wastecollection/](https://www.clacks.gov.uk/environment/wastecollection/) and enter your postcode. A list of matching properties is shown; use the **exact address text** shown in that list (commas and extra spaces are fine, they'll be normalised).

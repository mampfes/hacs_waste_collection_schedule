# Wyre Forest District Council

Support for schedules provided by [Wyre Forest District Council](https://www.wyreforestdc.gov.uk/), serving Wyre Forest district in Worcestershire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wyreforestdc_gov_uk
      args:
        street: UNIQUE_PROPERTY_REFERENCE_NUMBER
        town: POST_CODE
        garden_cutomer: HOUSE_NAME
```

### Configuration Variables

**street**  
*(string) (required)*

**town**  
*(string) (required)*

**street** and **town** should match the url parameters when clicking on an address here: <https://forms.wyreforestdc.gov.uk/querybin.asp>

**garden_cutomer**  
*(string) (optional)*

This is required if you want to show garden waste collections.

#### How to find your `garden_cutomer` id

Go to <https://forms.wyreforestdc.gov.uk/gardenwastechecker> enter your postcode and `select` your address. Before pressing Select open your developer tools (right click -> inspect (or press F12)) and go to the network tab. Press the `select` button on the webpage and you will see a POST request to `https://forms.wyreforestdc.gov.uk/GardenWasteChecker/Home/Details`. You can see your `garden_cutomer` id in the request payload.

## Example with garden waste

```yaml
waste_collection_schedule:
    sources:
    - name: wyreforestdc_gov_uk
      args:
        street: "hilltop avenue"
        town: "BEWDLEY"
        garden_cutomer: 308072
```

## Example without garden waste

```yaml
waste_collection_schedule:
    sources:
    - name: wyreforestdc_gov_uk
      args:
        street: "WORCESTER STREET"
        town: "STOURPORT ON SEVERN"
```

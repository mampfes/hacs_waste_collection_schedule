# South Kesteven District Council

Support for schedules provided by [South Kesteven District Council](https://southkesteven.gov.uk)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southkesteven_gov_uk
      args:
        address_id: ADDRESS_ID
```

### Configuration Variables

**address_id**  
*(int|string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: southkesteven_gov_uk
      args:
        address_id: "33399"
```

## How to find your `address_id`

Go to the [South Kesteven bin collection](https://pre.southkesteven.gov.uk/BinSearch.aspx) website and open search for your address. Either inspect the page where you would select your address (after postcode search) where you can find the `address_id` as value of the `value` attribute of the `option` tag containing your address. Alternatively, you can switch to the network tab of your browser's developer tools and click on "View your bin days" to see the request to the server. The `address_id` is in the payload of the request.

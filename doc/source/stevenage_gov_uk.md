# Stevenage Borough Council

Support for schedules provided by [Stevenage Borough Council](https://stevenage-self.achieveservice.com/service/my_bin_collection_schedule).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stevenage_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

Unique property reference. This is required.

To obtain this value, visit https://stevenage-self.achieveservice.com/service/my_bin_collection_schedule, enter your postcode and Inspect the Select address field. The value of the option associated with your address is your uprn.

For example, the UPRN in this example for 100 High Street is **200000586516**
```html
<option value="">Select...</option>
<option class="lookup-option" value="100080885553">10 High Street, Stevenage</option>
<option class="lookup-option" value="200000586516">100 High Street, Stevenage</option>
<option class="lookup-option" value="100081247651">101 High Street, Stevenage</option>
...
```

It can also be obtained via a search engine like [findmyaddress.co.uk](https://www.findmyaddress.co.uk/search).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stevenage_gov_uk
      args:
        uprn: 100080879233
```

# Durham County Council

Support for schedules provided by [Durham County Council](https://www.durham.gov.uk/article/1866/Household-bin-collections), serving Durham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: durham_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables
**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: durham_gov_uk
      args:
        uprn: "100110414978"
```

## How to find your `UPRN`

Your Unique Property Reference Number (UPRN) is displayed in the url when you search for your bin collection dates on the council web site.

For example: _www.durham.gov.uk/bincollections?uprn=`100110414978`#localityInformation_

Alternatively, you can your UPRN  by going to <https://www.findmyaddress.co.uk/> and entering your address details.
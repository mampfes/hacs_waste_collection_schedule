# iWeb iTouchVision

Consolidated support for schedules provided by Somerset Council and Test Valley District Council

Note: Somerset Council comprises four former District Councils (Mendip, Sedgemoor, Somerset West & Taunton, South Somerset) and Somerset County Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: iweb_itouchvision_com
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        council: COUNCIL
```

### Configuration Variables

**postcode**
*(string) (required)*


**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.


**council**
*(string) (required)*

Ensures the correct collection service is queried: Valid entries are:
 - "SOMERSET"
 - "TEST_VALLEY"




## Example

```yaml
waste_collection_schedule:
    sources:
    - name: iweb_itouchvision_com
      args:
        postcode: "TA20 2JG"
        uprn: "30071283"
        council: "SOMERSET"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

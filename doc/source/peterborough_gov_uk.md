# Peterborough City Council

Support for schedules provided by [Peterborough City Council](https://www.peterborough.gov.uk/bins-waste-and-recycling/household-waste/bin-collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: peterborough_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        post_code: POST_CODE
        name: HOUSE_NAME  # Legacy arg
        number: HOUSE_NUMBER  # Legacy arg
```

### Configuration Variables

**uprn**  
*(string) (required)*

The "Unique Property Reference Number" for your address. 

**post_code**  
*(string) (required)*

The postcode for your property.

**name**  
*legacy arg (string) (optional)*

The name of your property if you do not have a house number.
No longer required.

**number**  
*legacy arg (string) (optional)*

The house number of your property. No longer required.


#### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can inspect the web requests the Peterborough Council website makes when entering in your postcode and then selecting your address.

#### 2025 Peterborough City Council Website Updates
Peterborough changed their website api in July 2025 and queries now require both the UPRN and Postcode.
For historic configs that supplied just the UPRN, the script will use the UPRN to approximate a postcode.
For historic configs that supplied a postcode and name|number, the script will use the postcode to approximate a UPRN.
For more accurate results, consider updating your config to use your specific UPRN and Postcode.


## Example using preferred method (Postcode & UPRN)

```yaml
waste_collection_schedule:
    sources:
    - name: peterborough_gov_uk
      args:
        postcode: "PE5 7AX"
        uprn: 100090214774
```

## Example using legacy method (address config)

```yaml
waste_collection_schedule:
    sources:
    - name: peterborough_gov_uk
      args:
        post_code: PE57AX
        number: 1
```

## Example using legacy method (UPRN config)

```yaml
waste_collection_schedule:
    sources:
    - name: peterborough_gov_uk
      args:
        uprn: 100090214774
```

#### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can inspect the website url when the Peterborough Council website displays your collection schedule. The url has the format `report.peterborough.gov.uk/waste/postcode:uprn`.
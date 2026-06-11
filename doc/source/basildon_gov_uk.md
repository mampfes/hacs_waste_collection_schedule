# Basildon Council

Support for schedules provided by [Basildon Council](https://www3.basildon.gov.uk/website2/postcodes.nsf/frmMyBasildon), Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new South West Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

or

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**uprn**  
*(string) (required if postcode and address is not provided)*

**postcode**  
*(string) (required if no uprn provided)*

**address**  
*(string) (required if no uprn provided)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
      args:
        uprn: "100090277795"
```

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
      args:
        postcode: "SS14 1QU"
        address: "25 LONG RIDING"
```

## How to get the source arguments

### Using postcode and address

Go to <https://mybasildon.powerappsportals.com/check/where_i_live/> and enter your postcode and address. Then use the postcode and address as arguments.

### Using UPRN

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

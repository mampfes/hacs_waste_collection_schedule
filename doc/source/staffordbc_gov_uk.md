# Stafford Borough Council

Support for schedules provided by [Stafford Borough Council](https://www.staffordbc.gov.uk/)

# Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: staffordbc_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stafford_gov_uk
      args:
        uprn: "100031780029"
```

## How to get the source argument

The UPRN code can be found in the page by entering your postcode on the
[Stafford Borough Council 'About My Area'](https://www.staffordbc.gov.uk/about-my-area) page

Enter your postcode and then select your house from the list, then the UPRN is the final part of
the URL that you are re-directed to.

For example, for post-code ST16 3ES, house number 6, you are re-directed to


https://www.staffordbc.gov.uk/address/100031780029

The UPRN is 100031780029

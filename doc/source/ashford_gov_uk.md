# Ashford Borough Council

Support for schedules provided by [Ashford Borough Council](https://ashford.gov.uk), serving Ashford, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ashford_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**postcode**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ashford_gov_uk
      args:
        uprn: 100060796052
        postcode: TN23 3DY
        
```

## How to get the source argument

Use your postcode as `postcode` argument.

### How to get your UPRN

#### From external website

Find the parameter of your address using <https://secure.ashford.gov.uk/wastecollections/collectiondaylookup/> and write them exactly like on the web page.

#### From browser request analasys

- Go to <https://secure.ashford.gov.uk/wastecollections/collectiondaylookup/>.
- Insert you postcode and click `Continue`.
- Open your browsers Inspection tools (`F12` or `right click -> inspect`) and select the network tab.
- Select your address and click `continue`.
- You should now see multiple requests in the network tab. The first one should be (`POST`) `collectiondaylookup/`, select it.
- Select the `Payload` tab of this request.
- You can find your UPRN after `CollectionDayLookup2$DropDownList_Addresses:`

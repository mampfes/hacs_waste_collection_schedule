# East Lothian

Support for schedules provided by [East Lothian](https://www.eastlothian.gov.uk/), serving East Lothian, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastlothian_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        address_id: ADDRESS ID
        
```

### Configuration Variables

**postcode**  
*(String) (optional|recomendet)* **required if address_id is not provided**

**address**  
*(String) (optional|recomendet)* **required if address_id is not provided**

**address_id**  
*(String) (optional)* **will be used if provided (overrides postcode and address)**

## Example

### Using postcode and address (recommended)

```yaml
waste_collection_schedule:
    sources:
    - name: eastlothian_gov_uk
      args:
        postcode: EH21 8GU
        address: 4 Laing Loan, Wallyford
```

### Using address ID

```yaml
waste_collection_schedule:
    sources:
    - name: eastlothian_gov_uk
      args:
      address_id: ELC-C26071
```

## How to get the source argument

### Postcode and Address (recommended)

Go to [http://collectiondates.eastlothian.gov.uk/your-calendar](http://collectiondates.eastlothian.gov.uk/your-calendar) and enter your postcode and select your address from the list. The postcode and address should exactly match the results shown.

### Address ID

You can use the address ID directly. By going to the same page as above and opening the developer tools (F12 / right click -> inspect), you can find the address ID as value of the address corresponding `<option>` tag.

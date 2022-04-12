# AWB Limburg-Weilburg

Support for schedules provided by [awb-lm.de](https://www.awb-lm.de/) located in Hessen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_lm_de
      args:
        district: DISTRICT_ID
        city: CITY_ID
        street: STREET_ID
```

### Configuration Variables

**district**<br>
*(int) (required)*

**city**<br>
*(int) (required)*

**street**<br>
*(int) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_lm_de
      args:
        district: 1
        city: 47
        street: 1384
```


## How to get the source arguments

Visit [Abfuhrtermine](https://www.awb-lm.de/generator/abfuhrtermine.php), put in your address and press "Abfuhrtermine anzeigen".

Next right-click on the first dropdown and select "Inspect". Open the collapsed select-element in your browsers inspect-window. You'll find all the districts with their IDs, for example district "Limburg" with district ID 9:
```html
<option value="9">Limburg</option>
```
Repeat these steps for your city and street to get the correct IDs.
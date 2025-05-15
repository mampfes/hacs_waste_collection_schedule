# VMAB

This is a waste collection schedule integration for VMAB, servicing Blekinge, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vmab_se
      args:
        address: STREET_ADDRESS
        pickup_id: PICKUP_ID
```

### Configuration Variables

**address**  
*(string) (required)*

**pickup_id**  
*(string) (optional)*

### Note on optional parameter

The pickup_id variable is optional, but for the configuration to work it is required.
This is a secret id that is visible in the website's source code. If you leave this parameter as an empty string an error will be reported to the logs with alternatives you can choose from, saving you the trouble of reading source code.

For advanced users, you can adapt the following cURL command to get your pickup_id.

```bash
curl 'https://cal.vmab.se/search_suggestions.php' --compressed -X POST --data-raw 'search_address=Kvarnv%C3%A4gen+1+Laxens+Hus'
```

The id you are looking for is in id attribute of the list item. 

```html
<li class="selected" id="801602949">
```

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: vmab_se
      args:
        address: Kvarnvägen 1 Laxens Hus
        pickup_id: 801602949
```

## How to get the correct address

To find your correct address, search for it on the [VMAB page](https://cal.vmab.se/).
Please note that you will be given a suggestion box containing the address AND city you are searching for, but the City should be omitted in this source.
If you search on a "complete" address, e.g "Kvarnvägen 1 Laxens Hus Mörrum" you will get no matches. Please use only "Kvarnvägen 1 Laxens Hus".

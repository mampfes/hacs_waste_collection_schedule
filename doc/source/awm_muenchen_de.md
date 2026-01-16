# Abfallwirtschaftsbetrieb München

Support for schedules provided by [Abfallwirtschaftsbetrieb München](https://www.awm-muenchen.de/), Germany.


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: STREET
        house_number: HNR
        b_collection_cycle_string: COLLECTION CYCLE STRING organic waste bin
        p_collection_cycle_string: COLLECTION CYCLE STRING paper bin
        r_collection_cycle_string: COLLECTION CYCLE STRING residual waste bin
        b_location_id: LOCATION ID organic waste bin
        p_location_id: LOCATION ID paper bin
        r_location_id: LOCATION ID residual waste bin
```

### Configuration Variables

* **street**: Provide your street name (e.g., "Maxhofstraße")  
  *(string) (required)*
* **house_number**: Provide your house number  
  *(string) (required)*
* **b_collection_cycle_string**: provide the collection cycle string for the *organic waste bin* (see below)  
  *(string) (optional) (default: "")*
* **p_collection_cycle_string**: provide the collection cycle string for the *paper bin* (see below)  
  *(string) (optional) (default: "")*
* **r_collection_cycle_string**: provide the collection cycle string for the *residual waste bin* (see below)  
  *(string) (optional) (default: "")*
* **b_location_id**: provide the location ID numeric string for the *organic waste bin* (see below)  
  *(string) (optional) (default: "")*
* **p_location_id**: provide the location ID numeric string for the *paper bin* (see below)  
  *(string) (optional) (default: "")*
* **r_location_id**: provide the location ID numeric string for the *residual waste bin* (see below)  
  *(string) (optional) (default: "")*

> [!TIP]
> You should try to set up the integration through the UI with only the street name and the house number first. If you're lead to the setup of the sensors, that already worked.

## How to get the optional configuration arguments

However, some addresses require additional arguments, such as the the location ID numeric strings and / or collection cycle strings.

### Method 1 - guided process

Normally, if you submit the form to set up the integration or the new hub, the service will:
* Query the AWM server for a required parameter,
* give you an error message indicating that a form value is missing,
* and fill the form field drop down with suitable values for you to select.

> [!TIP]
> This needs to be done one form field at a time, so worst case, you need to submit the form 7 times.

### Method 2 - manual retrieval

Unfortunately, sometimes this does not work. To get the 6 optional parameters in case the previous method failed, please follow these steps:

* Navigate to https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/abfuhrkalender
* Enter your street name and house number
* Submit the form
* Select the correct location(s) for all three bins
* Submit the form
* locate the `Download ICS` button and copy its HTML link
* Use https://urlprettyprint.com/ to conveniently view the link parameters
  * The collection cycle parameters are contained in `tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][B|P|R]`
  * The location ID parameters are contained in `tx_awmabfuhrkalender_abfuhrkalender[stellplatz][bio|papier|restmuell]`

Enter these values into the respective form fields in the configuration UI, and you should be good to go.

## Examples

### Waltenbergerstr. 1 (no additional data required)

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Waltenbergerstr."
        house_number: "1"
```

### Marienplatz 1 with collection cycle string options set

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Marienplatz"
        house_number: "1"
        r_collection_cycle_string: "001;U",
        p_collection_cycle_string: "002;U"
```

### Bellinzonastr. 19 with location ID options set

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Bellinzonastr."
        house_number: "19"
        b_location_id: "70050134"
        p_location_id: "70050134"
        r_location_id: "70050134"

```
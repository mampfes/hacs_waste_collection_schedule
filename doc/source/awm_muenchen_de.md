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
        b_collect_cycle: COLLECTION CYCLE STRING organic waste bin
        p_collect_cycle: COLLECTION CYCLE STRING paper bin
        r_collect_cycle: COLLECTION CYCLE STRING residual waste bin
        bio_location_id: LOCATION ID organic waste bin
        papier_location_id: LOCATION ID paper bin
        restmuell_location_id: LOCATION ID residual waste bin
```

### Configuration Variables

* **street**: Provide your street name, abbreviated with a trailing decimal (e.g., "Maxhofstr.")  
  *(string) (required)*
* **house_number**: Provide your house number  
  *(string) (required)*
* **b_collect_cycle**: provide the collection cycle string for the *organic waste bin* (see below)  
  *(string) (optional) (default: "")*
* **p_collect_cycle**: provide the collection cycle string for the *paper bin* (see below)  
  *(string) (optional) (default: "")*
* **r_collect_cycle**: provide the collection cycle string for the *residual waste bin* (see below)  
  *(string) (optional) (default: "")*
* **bio_location_id**: provide the location ID numeric string for the *organic waste bin* (see below)  
  *(string) (optional) (default: "")*
* **papier_location_id**: provide the location ID numeric string for the *paper bin* (see below)  
  *(string) (optional) (default: "")*
* **restmuell_location_id**: provide the location ID numeric string for the *residual waste bin* (see below)  
  *(string) (optional) (default: "")*

You should try to set up the integration through the UI with only the street name and the house number first. If you're lead to the setup of the sensors, that already worked.

## How to get the optional configuration arguments

However, some addresses require additional arguments, such as the collection cycle strings and the location ID numeric strings.

Unfortunately, the strings for the collection cycle are not displayed in the web page of AWM. To get the 6 optional parameters in case the previous step failed, please follow these steps:

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

### Neureutherstr. 8 with a collection cycle option

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Neureutherstr."
        house_number: "8"
        r_collect_cycle: "1/2;G"
```

### Bellinzonastr. 19 with a collection cycle option

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Bellinzonastr."
        house_number: "19"
        b_collect_cycle: "1/2;G"
        p_collect_cycle: "1/2;U"
        r_collect_cycle: "001;U"
        bio_location_id: "70050134"
        papier_location_id: "70050134"
        restmuell_location_id: "70050134"

```
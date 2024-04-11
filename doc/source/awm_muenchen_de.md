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
        b_collect_cycle: COLLECTION CYCLE ID
        p_collect_cycle: COLLECTION CYCLE ID
        r_collect_cycle: COLLECTION CYCLE ID
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**b_collect_cycle**  
*(string) (optional) (default: "")*

**p_collect_cycle**  
*(string) (optional) (default: "")*

**r_collect_cycle**  
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Waltenbergerstr."
        house_number: "1"
    - name: awm_muenchen_de
      args:
        street: "Neureutherstr."
        house_number: "8"
        r_collect_cycle: "1/2;G"
```

Some addresses have different bin collection cycles (ex: weekly, bi-weekly). For these addresses the optional parameters are required.

## How to get the optional configuration arguments

 - Setup the component without the optional parameter and restart Home Assistant
 - Check the Home Assistant log for entries from this component.
 - The available options are listed in the error message.
 - Adjust the configuration and restart Home Assistant.
 
## Examples

### Waltenbergerstr. 1

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Waltenbergerstr."
        house_number: "1"
```

### Neureutherstr. 8 with an collection cycle option

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: "Neureutherstr."
        house_number: "8"
        r_collect_cycle: "1/2;G"
```

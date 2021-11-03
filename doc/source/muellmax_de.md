# Müllmax

Support for schedules provided by [muellmax.de](https://www.muellmax.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muellmax_de
      args:
        service: SERVICE
        mm_frm_ort_sel: ORT_SEL
        mm_frm_str_sel: STR_SEL
        mm_frm_hnr_sel: HNR_SEL
```

### Configuration Variables

**service**<br>
*(string) (required)*

**mm_frm_ort_sel**<br>
*(string) (optional)*

**mm_frm_str_sel**<br>
*(string) (optional)*

**mm_frm_hnr_sel**<br>
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellmax_de
      args:
        service: Fes
        mm_frm_str_sel: Achenbachstraße
        mm_frm_hnr_sel: 60596;Sachsenhausen;2;
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/muellmax_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/muellmax_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

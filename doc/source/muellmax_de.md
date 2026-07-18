# Müllmax

Support for schedules provided by [Müllmax](https://www.muellmax.de).

Source for Müllmax waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muellmax_de
      args:
        service: SERVICE
        mm_frm_ort_sel: MM_FRM_ORT_SEL
        mm_frm_str_sel: MM_FRM_STR_SEL
        mm_frm_hnr_sel: MM_FRM_HNR_SEL
```

### Configuration Variables

**service**  
*(string) (required)*

**mm_frm_ort_sel**  
*(string) (optional)*

**mm_frm_str_sel**  
*(string) (optional)*

**mm_frm_hnr_sel**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellmax_de
      args:
        service: Usb
        mm_frm_str_sel: "Freiligrathstra\xDFe"
        mm_frm_hnr_sel: 44791;Innenstadt;55;
```

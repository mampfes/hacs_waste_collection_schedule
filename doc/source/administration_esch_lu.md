# administration.esch.lu
Support for the Esch sur Alzette communal website in Luxembourg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: administration_esch_lu
      args:
        zone: A
```
### Configuration Variables

There is currenly only one conficuration variable, which is *zone*, which accepts only two chars - A or B.

**zone**
*(char) (required)*

This variable indicates collection zone. The city is divided by two zones with different collection schedule.
One can identify their zone prior to configuring here:
https://administration.esch.lu/dechets/

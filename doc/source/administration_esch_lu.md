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

## Sensor setup
There are following types of garbage parsed:
- Poubelle ménage
- Papier
- Organique
- Verre
- Valorlux
- Déchets toxiques
- Container ménage

Here is the example of sensors in `configuration.yaml`:

```yaml
sensor:
  - platform: waste_collection_schedule
    name: waste_organics
    count: 2
    add_days_to: True
    types:
      - Organique
  - platform: waste_collection_schedule
    name: waste_glass
    add_days_to: True
    count: 2
    types:
      - Verre
  - platform: waste_collection_schedule
    name: waste_valorlux
    add_days_to: True
    count: 2
    types:
      - Valorlux
  - platform: waste_collection_schedule
    name: waste_paper
    add_days_to: True
    count: 2
    types:
      - Papier
  - platform: waste_collection_schedule
    name: waste_household
    add_days_to: True
    count: 2
    types:
      - Poubelle ménage
```

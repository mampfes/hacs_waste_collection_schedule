# Entsorgungszweckverband der Gemeinden Liechtensteins (EZV)

Support for schedules provided by [Entsorgungszweckverband der Gemeinden Liechtensteins (EZV)](https://www.ezv.li/abfallentsorgung/abfallkalender/).

Source for the waste collection calendar of the EZV, Liechtenstein.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltransport_li
      args:
        municipality: MUNICIPALITY
        waste_type: WASTE_TYPE
```

### Configuration Variables

**municipality**  
*(string) (required)*

**waste_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltransport_li
      args:
        municipality: balzers
        waste_type: kehricht
```

## How to get the source arguments

Enter your municipality in lower case (balzers, triesen, triesenberg, vaduz, schaan, planken, gamprin-bendern, ruggell, mauren-schaanwald, eschen-nendeln or schellenberg). The waste type is optional: 'kehricht' (default), 'gruenabfuhr', 'all' or a comma-separated list. See https://www.ezv.li/abfallentsorgung/abfallkalender/ for the schedule.

# Heinz-Entsorgung (Landkreis Freising)

Support for schedules provided by [Heinz-Entsorgung (Landkreis Freising)](https://abfallkalender.heinz-entsorgung.de/).

Source for Heinz-Entsorgung (Landkreis Freising) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: heinz_entsorgung_de
      args:
        param: PARAM
```

### Configuration Variables

**param**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: heinz_entsorgung_de
      args:
        param: yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J
```

## How to get the source arguments

Open https://abfallkalender.heinz-entsorgung.de/ with the browser's developer tools (F12, Network tab), select your town and street, and copy the 'param' value of the request to api-enttermine.heinz-entsorgung.net/termine.

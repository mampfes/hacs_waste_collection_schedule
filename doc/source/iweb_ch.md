# i-web (Swiss municipalities)

Support for schedules provided by [i-web (Swiss municipalities)](https://www.i-web.ch).

Source for Swiss municipalities whose website runs on the i-web CMS and lists collection dates on its /abfalldaten page.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: iweb_ch
      args:
        website: WEBSITE
```

### Configuration Variables

**website**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: iweb_ch
      args:
        website: https://www.uetikonamsee.ch
```

## How to get the source arguments

Enter your municipality's website, e.g. https://www.flums.ch. It works if https://<website>/abfalldaten shows a table of collection dates.

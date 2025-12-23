# Entsorgungstermine Jena

Entsorgungstermine Jena is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://entsorgungstermine.jena.de> and select your address.
- For all bin types do not select any bin type
- Copy the link of the `ICS Jahr` button
- Use this link as the `url` parameter.

## Examples

### Altenburger Strasse 15-19

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://entsorgungstermine.jena.de/makeICSAll??x=true&street=Altenburger+Stra%C3%9Fe&hnummer=15-19
```

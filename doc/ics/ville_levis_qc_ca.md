# Lévis / Québec

Lévis / Québec is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.ville.levis.qc.ca/environnement-et-collectes/collectes/horaire-frequence/#c12646> figure out your collection day.
- Scroll down to `Synchronisez votre calendrier des collectes` section.
- Click on the collection day relevant for you and select `Copier l'url`.
- Use this copied URL as the `url` parameter.
- You may get shorter entries when using the `regex` parameter. and set it to `(.*?) |.*` to filter out everything after the first pipe `|` (including the pipe).

## Examples

### Jeudi : Lévis

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*?) |.*
        url: https://outlook.office365.com/owa/calendar/a61946ab1cc04c3685fa33ec061275c0@ville.levis.qc.ca/ac1cf50f622c4ab288a11d76ef00b3ea17018323504597930208/calendar.ics
```

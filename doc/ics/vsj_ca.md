# Saint-Jérome (QC)

Saint-Jérome (QC) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- If you don't know your sector, go to `https://www.vsj.ca/carte-interactive/` and open the "Collectes" section to find it.
- Visit `https://www.vsj.ca/collectes/` to figure out your collection day.
- Scroll down to `Synchronisez votre calendrier des collectes avec votre agenda numérique` section.
- Right-click on your sector and select `Copy link`.
- Use this copied URL as the `url` parameter.

## Examples

### Secteur C

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*?) |.*
        url: https://outlook.office365.com/owa/calendar/473e2b73ee41410d94dde0e32e5f8535@vsj.ca/bfcb8fe31e5442b79e3ffeaabc7c275a3606310763774097302/calendar.ics
```

# Marktgemeinde Kirchberg am Wechsel

Marktgemeinde Kirchberg am Wechsel is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

Kirchberg am Wechsel provides separate ICS feeds for each waste type via the RISKommunal calendar system. The URLs below are fixed — no address lookup is needed.

To configure all waste types, add one source block per URL using the `ics` source:

| Waste type | URL |
|---|---|
| Biomüll | `https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI0OTI1Mzcx&gnr=1979&sprache=1` |
| Restmüll | `https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1MTQxMjUy&gnr=1979&sprache=1` |
| Papiertonne | `https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1MTQxMjU0&gnr=1979&sprache=1` |
| Gelber Sack | `https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI2NjA4NDkx&gnr=1979&sprache=1` |
| Sondermüll | `https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjIzNzUyNTQ3&gnr=1979&sprache=1` |

Use each URL as the `url` parameter in a separate `ics` source block.

## Examples

### Biomüll

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI0OTI1Mzcx&gnr=1979&sprache=1
```
### Restmüll

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1MTQxMjUy&gnr=1979&sprache=1
```
### Papiertonne

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1MTQxMjU0&gnr=1979&sprache=1
```
### Gelber Sack

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI2NjA4NDkx&gnr=1979&sprache=1
```
### Sondermüll

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.kirchberg-am-wechsel.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjIzNzUyNTQ3&gnr=1979&sprache=1
```

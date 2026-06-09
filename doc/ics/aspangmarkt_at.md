# Gemeinde Aspang-Markt

Gemeinde Aspang-Markt is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

Aspang Markt provides separate ICS feeds for each waste type. The URLs below are fixed — no address lookup is needed.

To configure all waste types, add one source block per URL:

| Waste type | URL |
|---|---|
| Bio-Tonne | `https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1MTcyNzEy&gnr=1970&sprache=1` |
| Papiertonne | `https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1NjAyNDcz&gnr=1970&sprache=1` |
| Gelber Sack / Gelbe Tonne | `https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI2NjAwOTQ5&gnr=1970&sprache=1` |
| Restmüll | `https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI0NTg1OTA1&gnr=1970&sprache=1` |

Use each URL as the `url` parameter in a separate `ics` source block.

## Examples

### Bio-Tonne

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1MTcyNzEy&gnr=1970&sprache=1
```
### Papiertonne

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI1NjAyNDcz&gnr=1970&sprache=1
```
### Gelber Sack

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI2NjAwOTQ5&gnr=1970&sprache=1
```
### Restmüll

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.aspangmarkt.at/system/web/CalendarService.ashx?aqn=UmlTS29tbXVuYWwuT2JqZWN0cy5LYWxlbmRlciwgUklTQ29tcG9uZW50cywgVmVyc2lvbj0xLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGw%3D&do=MjI0NTg1OTA1&gnr=1970&sprache=1
```

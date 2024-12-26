# ReCollect

ReCollect is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- To get the URL, search your address in the recollect form of your home town.
- Click "Get a calendar", then "Add to Google Calendar".
- The URL shown is your ICS calendar link, for example.
  ```plain
  https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics?client_id=6FBD18FE-167B-11EC-992A-C843A7F05606
  ```
- You can strip the client ID URL parameter to get the final URL: `https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics`

known to work with:
|Region|Country|URL|
|-|-|-|
|Ottawa, ON|Canada|[ottawa.ca](https://ottawa.ca/en/garbage-and-recycling/recycling/garbage-and-recycling-collection-calendar)|
|Simcoe County, ON|Canada|[simcoe.ca](https://www.simcoe.ca/dpt/swm/when)|
|City of Bloomington, IN|USA|[api.recollect.net/r/area/bloomingtonin](https://api.recollect.net/r/area/bloomingtonin)|
|City of Cambridge, MA|USA|[cambridgema.gov](https://www.cambridgema.gov/services/curbsidecollections)|
|City of Georgetown, TX|USA|[texasdisposal.com](https://www.texasdisposal.com/waste-wizard/)|
|City of Vancouver|Canada|[vancouver.ca](https://vancouver.ca/home-property-development/garbage-and-recycling-collection-schedules.aspx)|
|City of Nanaimo|Canada|[nanaimo.ca](https://www.nanaimo.ca/city-services/garbage-recycling/collectionschedule)|
|City of Austin|USA|[austintexas.gov](https://www.austintexas.gov/myschedule)|
|Middlesbrough|UK|[middlesbrough.gov.uk](https://my.middlesbrough.gov.uk/login/)|
|City of McKinney|USA|[mckinneytexas.org](https://www.mckinneytexas.org/503/Residential-Trash-Services/#App)|
|Waste Connections|USA|[wasteconnections.com](https://www.wasteconnections.com/pickup-schedule/)|
|Halton County, ON|Canada|[halton.ca](https://www.halton.ca/For-Residents/Recycling-Waste/Recycling-and-Waste-Tools/Online-Waste-Collection-Schedule)|
|District of Saanish, BC|Canada|[saanich.ca](https://www.saanich.ca/EN/main/community/utilities-garbage/garbage-organics-recycling.html)|
|Caerphilly, Wales|UK|[caerphilly.gov.uk](https://www.caerphilly.gov.uk/services/household-waste-and-recycling/bin-collection-days)|
|Recology CleanScapes, WA|USA|[recology.com](https://www.recology.com/recology-king-county/des-moines/collection-calendar/)|
|City of Lethbridge|Canada|[lethbridge.ca](https://www.lethbridge.ca/waste-recycling/#wastewizard)|
|City of Regina|Canada|[regina.ca](https://www.regina.ca/home-property/recycling-garbage/)|
|Hardin Sanitation, Ada County, Idaho|USA|[hardinsanitation.com/ada](https://www.hardinsanitation.com/ada/)|
|Hardin Sanitation, Treasure Valley, Idaho|USA|[hardinsanitation.com](https://www.hardinsanitation.com/home/)|
|Hardin Sanitation, City of Eagle, Idaho|USA|[hardinsanitation.com/cityofeagle](https://www.hardinsanitation.com/cityofeagle/)|


and probably a lot more.

## Examples

### Cambridge, MA, USA

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/F2BCBBF2-ACC9-11E8-B4BD-CFDD30C1D4D8/services/761/events.en-US.ics
```
### Ottawa, ON, Canada

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics
```
### Georgetown, TX, USA

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/9EA385D4-4AF9-11EB-B308-E6A235C11932/services/611/events.en-US.ics
```
### Sherwood Park, AB, Canada

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://recollect.a.ssl.fastly.net/api/places/F5A5C1D2-3D25-11EE-A377-8D1C706BDDF3/services/238/events.en.ics?client_id=7CCAFDAE-3D25-11EE-8AF8-9D1C706BDDF3
```
### Morris, MB, Canada

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: webcal://recollect.a.ssl.fastly.net/api/places/2DC90F42-E8AA-11EB-A726-598C8684B99B/services/397/events.en.ics
```
### Peterborough, ON, Canada

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: webcal://recollect.a.ssl.fastly.net/api/places/C0A33242-3365-11EC-A104-84C872B788E8/services/345/events.en.ics?client_id=F81035CA-7177-11EE-A247-E8E188BA1CF3
```
### 166 W 47th Ave, Vancouver

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://recollect.a.ssl.fastly.net/api/places/3734BF46-A9A1-11E2-8B00-43B94144C028/services/193/events.en.ics?client_id=8844492C-9457-11EE-90E3-08A383E66757
```
### Cathedral of Junk, Austin, TX

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/2587D9F6-DF59-11E8-96F5-0E2C682931C6/services/323/events.en-US.ics
```
### 3329 Sorghum Way, McKinney, TX

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://api.recollect.net/w/areas/WC-5183/services/995/pages/widget_subscribe_calendar?back_stack=%5B%5B%22place_calendar%22%2C%7B%22for%22%3A%22WC-5183%22%2C%22tabbed%22%3Atrue%7D%5D%5D#
```
### Halton Region, ON, Canada

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/97323326-A43B-11E2-A636-ABBA3CA4474E/services/224/events.en.ics?client_id=61BBBF46-7800-11EF-8692-290A842A7710
```
### District of Saanich, BC, Canada

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/46BC2620-B477-11E3-B3D4-47898BE95184/services/214/events.en.ics?client_id=BD5E38F8-741B-11EF-B562-C1575C8ED1CF
```
### Recology CleanScapes

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/6D1AA3AC-D794-11EC-AFDF-27CF02E3D7CF/services/282/events.en-US.ics?client_id=ABC6EE28-8A1E-11EF-844A-7A54B7F06687
```
### Hardin Sanitation, Idaho, USA

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: '\, (?:and )?|(?: and )'
        url: https://recollect.a.ssl.fastly.net/api/places/0495A9DC-DB0F-11E9-8172-34B19DD5B1B2/services/881/events.en-US.ics?
```

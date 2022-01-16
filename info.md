# Waste Collection Schedule

Waste Collection Schedule provides schedules from waste collection service providers to Home Assistant. Additionally, it supports schedules from generic ICS files which can be stored locally or fetched from a web site. There is a high flexibility in providing the information to be displayed.

## Examples

Per default (without further configuration), the time to the next collection will be shown in an [entity card](https://www.home-assistant.io/lovelace/entity/):

![Default Lovelace Card](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/default-entity.png)

You can also setup dedicated entities per waste type and show the schedule in various formats:

![Days to next collections](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/days-to-next-collections.png)
![Date of next collections](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/date-of-next-collections.png)
![Date and days to next collections](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/next-collections-date-and-days.png)

The information in the more-info popup can be displayed in different formats:

1. List of upcoming collections:

   ![More info: upcoming](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/more-info-upcoming.png)

2. List of waste types and collection date:

   ![More info: waste types](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/more-info-appointment-types.png)

[Button Card](https://github.com/custom-cards/button-card) can be used to create individual Lovelace cards:

![Button Card](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/button-cards.png)

## Documentation

- [Full Documentation](https://github.com/mampfes/hacs_waste_collection_schedule)

## Supported Service Providers

Currently the following service providers are supported:

- [Generic ICS / iCal File](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ics.md)

### Australia

- [Brisbane City Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/brisbane_qld_gov_au.md)
- [North Adelaide Waste Management Authority, South Australia](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/nawma_sa_gov_au.md)
- [The Hills Council, Sydney](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/thehills_nsw_gov_au.md)
- [Stonnington City Council, Melbourne](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stonnington_vic_gov_au.md)

### Belgium
- [Hygea](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/hygea_be.md)
- [Recycle! / RecycleApp.be](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/recycleapp_be.md)
### Germany

- [Abfall.IO / AbfallPlus.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_io.md)
- [AbfallNavi.de (RegioIT.de)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfallnavi_de.md)
- [Abfallwirtschaft Rendsburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awr_de.md)
- [Abfallwirtschaft Stuttgart](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stuttgart_de.md)
- [Abfallwirtschaft Südholstein](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awsh_de.md)
- [Abfallwirtschaft Zollernalbkreis](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_zollernalbkreis_de.md)
- [AWBKoeln.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awbkoeln_de.md)
- [AWIDO-online.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awido_de.md)
- [Berlin-Recycling.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/berlin_recycling_de.md)
- [BSR.de / Berliner Stadtreinigungsbetriebe](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/bsr_de.md)
- [EGN-Abfallkalender.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master//doc/source/egn_abfallkalender_de.md)
- [Jumomind.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/jumomind_de.md)
- [Landkreis-Wittmund.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/landkreis_wittmund_de.md)
- [Muellmax.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/muellmax_de.md)
- [MyMuell App](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/jumomind_de.md)
- [Rhein-Hunsrück Entsorgung (RHE)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/rh_entsorgung_de.md)
- [Sector27.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/sector27_de.md)
- [Stadtreinigung.Hamburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtreinigung_hamburg.md)
- [Stadtreinigung-Leipzig.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtreinigung_leipzig_de.md)
- [WAS Wolfsburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/was_wolfsburg_de.md)

### Netherlands

- [Ximmio](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ximmio_nl.md)
- [HVCGroep](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/hvcgroep_nl.md)

### New Zealand

- [Auckland](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/aucklandcouncil_govt_nz.md)
- [Christchurch](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ccc_govt_nz.md)
- [Gore, Invercargill & Southland](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/wastenet_org_nz.md)

### Sweden
- [Lerum.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/lerum_se.md)
- [Sysav.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/sysav_se.md)

### Switzerland
- [Lindau.ch](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/lindau_ch.md)

### United States of America

- [PGH.ST](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/pgh_st.md)
- [Seattle Public Utilities](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/seattle_gov.md)

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
- [Static source](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/static.md)

### Australia

- [Banyule City Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/banyule_vic_gov_au.md)
- [Belmont City Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/belmont_wa_gov_au.md)
- [Brisbane City Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/brisbane_qld_gov_au.md)
- [Campbelltown City Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/campbelltown_nsw_gov_au.md)
- [City of Canada Bay Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/canadabay_nsw_gov_au.md)
- [Inner West Council (NSW)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/innerwest_nsw_gov_au.md)
- [Ku-ring-gai Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/kuringgai_nsw_gov_au.md)
- [Macedon Ranges Shire Council, Melbourne](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/mrsc_vic_gov_au.md)
- [Maroondah City Council](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/maroondah_vic_gov_au.md)
- [Melton City Council, Melbourne](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/melton_vic_gov_au.md)
- [Nillumbik Shire Council, Melbourne](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/nillumbik_vic_gov_au.md)
- [North Adelaide Waste Management Authority, South Australia](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/nawma_sa_gov_au.md)
- [RecycleSmart](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/recyclesmart.md)
- [Stonnington City Council, Melbourne](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stonnington_vic_gov_au.md)
- [Sunshine Coast, Queensland](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/sunshinecoast_qld_gov_au.md)
- [The Hills Council, Sydney](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/thehills_nsw_gov_au.md)
- [Wyndham City Council, Melbourne](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/sourcewyndham_vic_gov_au.md)

### Austria

- [BMV.at](https://github.com/mampfes/hacs_waste_collection_schedule/doc/source/bmv_at.md)
- [Data.Umweltprofis](https://github.com/mampfes/hacs_waste_collection_schedule/doc/source/data_umweltprofis_at.md)
- [Korneuburg Stadtservice](https://github.com/mampfes/hacs_waste_collection_schedule/doc/source/korneuburg_stadtservice_at.md)
- [WSZ-Moosburg.at](https://github.com/mampfes/hacs_waste_collection_schedule/doc/source/wsz_moosburg_at.md)

### Belgium

- [Hygea](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/hygea_be.md)
- [Recycle! / RecycleApp.be](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/recycleapp_be.md)

### Canada
- [City of Toronto](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/toronto_ca.md)

### Germany

- [Abfall.IO / AbfallPlus.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_io.md)
- [AbfallNavi.de (RegioIT.de)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfallnavi_de.md)
- [Abfallkalender Würzburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/wuerzburg_de.md)
- [Abfalltermine Forchheim](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfalltermine_forchheim_de.md)
- [Abfallwirtschaft Bremen](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/c_trace_de.md)
- [Abfallwirtschaft Landkreis Harburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/aw_harburg_de.md)
- [Abfallwirtschaft Landkreis Wolfenbüttel](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/alw_wf_de.md)
- [Abfallwirtschaft Neckar-Odenwald-Kreis](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awn_de.md)
- [Abfallwirtschaft Rendsburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awr_de.md)
- [Abfallwirtschaft Stuttgart](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stuttgart_de.md)
- [Abfallwirtschaft Südholstein](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awsh_de.md)
- [Abfallwirtschaft Zollernalbkreis](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_zollernalbkreis_de.md)
- [Alb-Donau-Kreis](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/buergerportal_de.md)
- [ART Trier](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/art_trier_de.md)
- [AWB Bad Kreuznach](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awb_bad_kreuznach_de.md)
- [AWB Esslingen](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awb_es_de.md)
- [AWB Limburg-Weilburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awb_lm_de.md)
- [AWB Oldenburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awb_oldenburg_de.md)
- [AWBKoeln.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awbkoeln_de.md)
- [AWIDO-online.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awido_de.md)
- [Berlin-Recycling.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/berlin_recycling_de.md)
- [Biedenkopf MZV](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/buergerportal_de.md)
- [Bogenschuetz-Entsorgung.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/infeo_at.md)
- [BSR.de / Berliner Stadtreinigungsbetriebe](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/bsr_de.md)
- [C-Trace.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/c_trace_de.md)
- [Cochem-Zell](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/buergerportal_de.md)
- [EGN-Abfallkalender.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/egn_abfallkalender_de.md)
- [Erlangen-Höchstadt](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/erlangen_hoechstadt_de.md)
- [Jumomind.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/jumomind_de.md)
- [KWB-Goslar.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/kwb_goslar_de.md)
- [KWU-Entsorgung.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/kwu_de.md)
- [KAEV Niederlausitz](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/kaev_niederlausitz_de.md)
- [Landkreis-Wittmund.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/landkreis_wittmund_de.md)
- [Landkreis Rhön Grabfeld](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/landkreis_rhoen_grabfeld.md)
- [Landkreis Schwäbisch Hall](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/lrasha_de.md)
- [Muellmax.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/muellmax_de.md)
- [MyMuell App](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/jumomind_de.md)
- [Neunkirchen Siegerland](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_neunkirchen_siegerland_de.md)
- [RegioEntsorgung](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/regioentsorgung_de.md)
- [Rhein-Hunsrück Entsorgung (RHE)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/rh_entsorgung_de.md)
- [Sector27.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/sector27_de.md)
- [Stadtreinigung Dresden](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtreinigung_dresden_de.md)
- [Stadtreinigung.Hamburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtreinigung_hamburg.md)
- [Stadtreinigung-Leipzig.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtreinigung_leipzig_de.md)
- [Stadt-Willich.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadt_willich_de.md)
- [Stadtservice Brühl](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtservice_bruehl_de.md)
- [Städteservice Raunheim Rüsselsheim](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/staedteservice_de.md)
- [Südbrandenburgischer Abfallzweckverband](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/sbazv_de.md)
- [Umweltbetrieb Stadt Bielefeld](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/bielefeld_de.md)
- [WAS Wolfsburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/was_wolfsburg_de.md)
- [Wermelskirchen](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/wermelskirchen_de.md)
- [Zweckverband Abfallwirtschaft Werra-Meißner-Kreis](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/zva_wmk_de.md)

### Lithuania

- [Kauno švara](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/grafikai_svara_lt.md)

### Netherlands

- [HVCGroep and others](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/hvcgroep_nl.md)
- [Ximmio](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ximmio_nl.md)

### New Zealand

- [Auckland](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/aucklandcouncil_govt_nz.md)
- [Christchurch](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ccc_govt_nz.md)
- [Gore, Invercargill & Southland](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/wastenet_org_nz.md)
- [Horowhenua District](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/horowhenua_govt_nz.md)
- [Waipa District](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/waipa_nz.md)
- [Wellington](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/wellington_govt_nz.md)

### Norway

- [Min Renovasjon](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/minrenovasjon_no.md)
- [Oslo Kommune](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/oslokommune_no.md)

### Poland

- [Warsaw](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/warszawa19115_pl.md)
- [Multiple communities - ecoharmonogram](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ecoharmonogram_pl.md)

### Sweden

- [Lerum.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/lerum_se.md)
- [Ronneby Miljöteknik](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/miljoteknik_se.md)
- [srvatervinning.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/srvatervinning_se.md)
- [SSAM.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ssam_se.md)
- [Sysav.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/sysav_se.md)
- [Vasyd.se](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/vasyd_se.md)

### Switzerland

- [A-Region.ch](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/a_region_ch.md)
- [Lindau.ch](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/lindau_ch.md)

### United States of America

- [PGH.ST](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/pgh_st.md)
- [Republic Services](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/republicservices_com.md)
- [Seattle Public Utilities](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/seattle_gov.md)

### United Kingdom

- [Bracknell Forest Council - bracknell-forest.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/bracknell_forest_gov_uk.md)
- [Bradford Metropolitan District Council - bradford.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/bradford_gov_uk.md)
- [Braintree District Council - bracknell-forest.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/braintree_gov_uk.md)
- [Cambridge City Council - cambridge.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/cambridge_gov_uk.md)
- [Canterbury City Council - canterbury.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/canterbury_gov_uk.md)
- [Cheshire East Council - cheshireeast.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/cheshire_east_gov_uk.md)
- [Chesterfield Borough Council - chesterfield.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/chesterfield_gov_uk.md)
- [Colchester Borough Council - colchester.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/colchester_gov_uk.md)
- [Cornwall Council - cornwall.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/cornwall_gov_uk.md)
- [Derby City Council - derby.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/derby_gov_uk.md)
- [Eastbourne Borough Council - lewes-eastbourne.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/environmentfirst_co_uk.md)
- [Elmbridge Borough Council - elmbridge.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/elmbridge_gov_uk.md)
- [Guildford Borough Council - guildford.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/guildford_gov_uk.md)
- [Harborough District Council - www.harborough.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/fccenvironment_co_uk.md)
- [Huntingdonshire District Council - huntingdonshire.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/huntingdonshire_gov_uk.md)
- [The Royal Borough of Kingston Council - kingston.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/kingston_gov_uk.md)
- [Lewes District Council - lewes-eastbourne.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/environmentfirst_co_uk.md)
- [London Borough of Lewisham - lewisham.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/lewisham_gov_uk.md)
- [Manchester City Council - manchester.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/manchester_uk.md)
- [Middlesbrough Council - middlesbrough.gov.uk](https://www.middlesbrough.gov.uk/bin-collection-dates)
- [Newcastle City Council - newcastle.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/newcastle_gov_uk.md)
- [North Somerset Council - n-somerset.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/nsomerset_gov_uk.md)
- [North West Leicestershire - nwleics.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/nwleics_gov_uk.md)
- [Nottingham City Council - nottinghamcity.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/nottingham_city_gov_uk.md)
- [Peterborough City Council - peterborough.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/peterborough_gov_uk.md)
- [Reading Council - reading.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/reading_gov_uk.md)
- [Richmondshire District Council - richmondshire.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/richmondshire_gov_uk.md)
- [Rushmoor Borough Council - rushmoor.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/rushmoor_gov_uk.md)
- [Sheffield City Council - Sheffield.gov.uk]((https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/sheffield_gov_uk.md)
- [South Cambridgeshire District Council - scambs.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/scambs_gov_uk.md)
- [South Norfolk and Broadland Council - southnorfolkandbroadland.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/south_norfolk_and_broadland_gov_uk.md)
- [Stevenage Borough Council - stevenage.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stevenage_gov_uk.md)
- [Tewkesbury Borough Council](./doc/source/tewkesbury_gov_uk.md)
- [City of York Council - york.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/york_gov_uk.md)
- [Walsall Council - walsall.gov.uk](./doc/source/walsall_gov_uk.md)
- [West Berkshire Council - westberks.gov.uk](./doc/source/westberks_gov_uk.md)
- [Wiltshire Council - wiltshire.gov.uk](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/wiltshire_gov_uk.md)

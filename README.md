<!-- GitHub Markdown Reference: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github -->

<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Waste Collection Schedule

**A custom component for Home Assistant that retrieves waste collection schedules from a wide range of service providers.**

<img src="/images/wcs_animated.gif" alt="Waste Collection Schedule animation" title="Waste Collection Schedule" align="right" height="200" />

Waste collection schedules from service provider web sites are updated daily, derived from local ICS/iCal files, or generated from user-specified dates or regularly repeating date patterns. The Home Assistant built-in Calendar is automatically populated with schedules, and there is a high degree of flexibility in how information can be format and displayed in entity cards or pop-ups. The framework can easily be extended to support additional waste collection service providers, or other services which provide schedules.

# Supported Service Providers

Waste collection schedules in the following formats and countries are supported. Click on the section heading to view details of individual service providers.

<details>
<summary>ICS/iCal and User-Specified</summary>

- [Generic ICS / iCal File](/doc/source/ics.md)
- [User Specified](/doc/source/static.md)
</details>

<!--Begin of country section-->
<details>
<summary>Australia</summary>

- [Banyule City Council](/doc/source/banyule_vic_gov_au.md) / banyule.vic.gov.au
- [Belmont City Council](/doc/source/belmont_wa_gov_au.md) / belmont.wa.gov.au
- [Brisbane City Council](/doc/source/brisbane_qld_gov_au.md) / brisbane.qld.gov.au
- [Campbelltown City Council](/doc/source/campbelltown_nsw_gov_au.md) / campbelltown.nsw.gov.au
- [City of Canada Bay Council](/doc/source/canadabay_nsw_gov_au.md) / canadabay.nsw.gov.au
- [Gold Coast City Council](/doc/source/goldcoast_qld_gov_au.md) / goldcoast.qld.gov.au
- [Inner West Council (NSW)](/doc/source/innerwest_nsw_gov_au.md) / innerwest.nsw.gov.au
- [Ipswich City Council](/doc/source/ipswich_qld_gov_au.md) / ipswich.qld.gov.au
- [Ku-ring-gai Council](/doc/source/kuringgai_nsw_gov_au.md) / krg.nsw.gov.au
- [Macedon Ranges Shire Council](/doc/source/mrsc_vic_gov_au.md) / mrsc.vic.gov.au
- [Maroondah City Council](/doc/source/maroondah_vic_gov_au.md) / maroondah.vic.gov.au
- [Melton City Council](/doc/source/melton_vic_gov_au.md) / melton.vic.gov.au
- [Nillumbik Shire Council](/doc/source/nillumbik_vic_gov_au.md) / nillumbik.vic.gov.au
- [North Adelaide Waste Management Authority](/doc/source/nawma_sa_gov_au.md) / nawma.sa.gov.au
- [RecycleSmart](/doc/source/recyclesmart_com.md) / recyclesmart.com
- [Stonnington City Council](/doc/source/stonnington_vic_gov_au.md) / stonnington.vic.gov.au
- [The Hills Shire Council, Sydney](/doc/source/thehills_nsw_gov_au.md) / thehills.nsw.gov.au
- [Wyndham City Council, Melbourne](/doc/source/wyndham_vic_gov_au.md) / wyndham.vic.gov.au
</details>

<details>
<summary>Austria</summary>

- [Burgenländischer Müllverband](/doc/source/bmv_at.md) / bmv.at
- [infeo](/doc/source/infeo_at.md) / infeo.at
- [Stadtservice Korneuburg](/doc/source/korneuburg_stadtservice_at.md) / korneuburg.gv.at
- [Umweltprofis](/doc/source/data_umweltprofis_at.md) / umweltprofis.at
- [WSZ Moosburg](/doc/source/wsz_moosburg_at.md) / wsz-moosburg.at
</details>

<details>
<summary>Belgium</summary>

- [Hygea](/doc/source/hygea_be.md) / hygea.be
- [Recycle!](/doc/source/recycleapp_be.md) / recycleapp.be
</details>

<details>
<summary>Canada</summary>

- [City of Toronto](/doc/source/toronto_ca.md) / toronto.ca
</details>

<details>
<summary>Germany</summary>

- [Abfall Stuttgart](/doc/source/stuttgart_de.md) / service.stuttgart.de
- [Abfall.IO / AbfallPlus](/doc/source/abfall_io.md) / abfallplus.de
- [Abfallkalender Würzburg](/doc/source/wuerzburg_de.md) / wuerzburg.de
- [AbfallNavi (RegioIT.de)](/doc/source/abfallnavi_de.md) / regioit.de
- [Abfalltermine Forchheim](/doc/source/abfalltermine_forchheim_de.md) / abfalltermine-forchheim.de
- [Abfallwirtschaft Alb-Donau-Kreis](/doc/source/buergerportal_de.md) / aw-adk.de
- [Abfallwirtschaft Landkreis Harburg](/doc/source/aw_harburg_de.md) / landkreis-harburg.de
- [Abfallwirtschaft Landkreis Wolfenbüttel](/doc/source/alw_wf_de.md) / alw-wf.de
- [Abfallwirtschaft Neckar-Odenwald-Kreis](/doc/source/awn_de.md) / awn-online.de
- [Abfallwirtschaft Nürnberger Land](/doc/source/nuernberger_land_de.md) / nuernberger-land.de
- [Abfallwirtschaft Rendsburg](/doc/source/awr_de.md) / awr.de
- [Abfallwirtschaft Südholstein](/doc/source/awsh_de.md) / awsh.de
- [Abfallwirtschaft Werra-Meißner-Kreis](/doc/source/zva_wmk_de.md) / zva-wmk.de
- [Abfallwirtschaft Zollernalbkreis](/doc/source/abfall_zollernalbkreis_de.md) / abfallkalender-zak.de
- [Abfallwirtschaftsbetrieb Esslingen](/doc/source/awb_es_de.md) / awb-es.de
- [Abfallwirtschaftsbetrieb Landkreis Ahrweiler](/doc/source/meinawb_de.md) / meinawb.de
- [ART Trier](/doc/source/art_trier_de.md) / art-trier.de
- [AWB Bad Kreuznach](/doc/source/awb_bad_kreuznach_de.md) / app.awb-bad-kreuznach.de
- [AWB Köln](/doc/source/awbkoeln_de.md) / awbkoeln.de
- [AWB Landkreis Augsburg](/doc/source/c_trace_de.md) / awb-landkreis-augsburg.de
- [AWB Oldenburg](/doc/source/awb_oldenburg_de.md) / oldenburg.de
- [AWIDO Online](/doc/source/awido_de.md) / awido-online.de
- [Berlin Recycling](/doc/source/berlin_recycling_de.md) / berlin-recycling.de
- [Berliner Stadtreinigungsbetriebe](/doc/source/bsr_de.md) / bsr.de
- [Bielefeld](/doc/source/bielefeld_de.md) / bielefeld.de
- [Bogenschütz Entsorgung](/doc/source/infeo_at.md) / bogenschuetz-entsorgung.de
- [Bremener Stadreinigung](/doc/source/c_trace_de.md) / die-bremer-stadtreinigung.de
- [Bürgerportal](/doc/source/buergerportal_de.md) / c-trace.de
- [C-Trace](/doc/source/c_trace_de.md) / c-trace.de
- [EGN Abfallkalender](/doc/source/egn_abfallkalender_de.md) / egn-abfallkalender.de
- [Jumomind](/doc/source/jumomind_de.md) / jumomind.de
- [KAEV Niederlausitz](/doc/source/kaev_niederlausitz.md) / kaev.de
- [Kreiswirtschaftsbetriebe Goslar](/doc/source/kwb_goslar_de.md) / kwb-goslar.de
- [KV Cochem-Zell](/doc/source/buergerportal_de.md) / cochem-zell-online.de
- [KWU Entsorgung Landkreis Oder-Spree](/doc/source/kwu_de.md) / kwu-entsorgung.de
- [Landkreis Erlangen-Höchstadt](/doc/source/erlangen_hoechstadt_de.md) / erlangen-hoechstadt.de
- [Landkreis Nordwestmecklenburg](/doc/source/geoport_nwm_de.md) / geoport-nwm.de
- [Landkreis Rhön Grabfeld](/doc/source/landkreis_rhoen_grabfeld.md) / abfallinfo-rhoen-grabfeld.de
- [Landkreis Schwäbisch Hall](/doc/source/lrasha_de.md) / lrasha.de
- [Landkreis Wittmund](/doc/source/landkreis_wittmund_de.md) / landkreis-wittmund.de
- [MZV Bidenkopf](/doc/source/buergerportal_de.md) / mzv-biedenkopf.de
- [Müllmax](/doc/source/muellmax_de.md) / muellmax.de
- [Neunkirchen Siegerland](/doc/source/abfall_neunkirchen_siegerland_de.md) / neunkirchen-siegerland.de
- [RegioEntsorgung Städteregion Aachen](/doc/source/regioentsorgung_de.md) / regioentsorgung.de
- [Rhein-Hunsrück Entsorgung (RHE)](/doc/source/rh_entsorgung_de.md) / rh-entsorgung.de
- [Sector 27 - Datteln, Marl, Oer-Erkenschwick](/doc/source/sector27_de.md) / muellkalender.sector27.de
- [Stadt Willich](/doc/source/stadt_willich_de.md) / stadt-willich.de
- [Stadtreinigung Dresden](/doc/source/stadtreinigung_dresden_de.md) / dresden.de
- [Stadtreinigung Hamburg](/doc/source/stadtreinigung_hamburg.md) / stadtreinigung.hamburg
- [Stadtreinigung Leipzig](/doc/source/stadtreinigung_leipzig_de.md) / stadtreinigung-leipzig.de
- [StadtService Brühl](/doc/source/stadtservice_bruehl_de.md) / stadtservice-bruehl.de
- [Städteservice Raunheim Rüsselsheim](/doc/source/staedteservice_de.md) / staedteservice.de
- [Südbrandenburgischer Abfallzweckverband](/doc/source/sbazv_de.md) / sbazv.de
- [Wermelskirchen](/doc/source/wermelskirchen_de.md) / wermelskirchen.de
- [Wolfsburger Abfallwirtschaft und Straßenreinigung](/doc/source/was_wolfsburg_de.md) / was-wolfsburg.de
- [WZV Kreis Segeberg](/doc/source/c_trace_de.md) / wzv.de
</details>

<details>
<summary>Lithuania</summary>

- [Kauno švara](/doc/source/grafikai_svara_lt.md) / grafikai.svara.lt
</details>

<details>
<summary>Netherlands</summary>

- [ACV Group](/doc/source/ximmio_nl.md) / acv-afvalkalender.nl
- [Alpen an den Rijn](/doc/source/hvcgroep_nl.md) / alphenaandenrijn.nl
- [Area Afval](/doc/source/ximmio_nl.md) / area-afval.nl
- [Avalex](/doc/source/ximmio_nl.md) / avalex.nl
- [Avri](/doc/source/ximmio_nl.md) / avri.nl
- [Bar Afvalbeheer](/doc/source/ximmio_nl.md) / bar-afvalbeheer.nl
- [Cyclus NV](/doc/source/hvcgroep_nl.md) / cyclusnv.nl
- [Dar](/doc/source/hvcgroep_nl.md) / dar.nl
- [Den Haag](/doc/source/hvcgroep_nl.md) / denhaag.nl
- [GAD](/doc/source/hvcgroep_nl.md) / gad.nl
- [Gemeente Almere](/doc/source/ximmio_nl.md) / almere.nl
- [Gemeente Berkelland](/doc/source/hvcgroep_nl.md) / gemeenteberkelland.nl
- [Gemeente Cranendonck](/doc/source/hvcgroep_nl.md) / cranendonck.nl
- [Gemeente Hellendoorn](/doc/source/ximmio_nl.md) / hellendoorn.nl
- [Gemeente Lingewaard](/doc/source/hvcgroep_nl.md) / lingewaard.nl
- [Gemeente Meppel](/doc/source/ximmio_nl.md) / meppel.nl
- [Gemeente Middelburg + Vlissingen](/doc/source/hvcgroep_nl.md) / middelburgvlissingen.nl
- [Gemeente Peel en Maas](/doc/source/hvcgroep_nl.md) / peelenmaas.nl
- [Gemeente Schouwen-Duiveland](/doc/source/hvcgroep_nl.md) / schouwen-duiveland.nl
- [Gemeente Sudwest-Fryslan](/doc/source/hvcgroep_nl.md) / sudwestfryslan.nl
- [Gemeente Venray](/doc/source/hvcgroep_nl.md) / venray.nl
- [Gemeente Voorschoten](/doc/source/hvcgroep_nl.md) / voorschoten.nl
- [Gemeente Wallre](/doc/source/hvcgroep_nl.md) / waalre.nl
- [Gemeente Westland](/doc/source/ximmio_nl.md) / gemeentewestland.nl
- [HVC Groep](/doc/source/hvcgroep_nl.md) / hvcgroep.nl
- [Meerlanden](/doc/source/ximmio_nl.md) / meerlanden.nl
- [Mijn Blink](/doc/source/hvcgroep_nl.md) / mijnblink.nl
- [PreZero](/doc/source/hvcgroep_nl.md) / prezero.nl
- [Purmerend](/doc/source/hvcgroep_nl.md) / purmerend.nl
- [RAD BV](/doc/source/ximmio_nl.md) / radbv.nl
- [Reinigingsbedrijf Midden Nederland](/doc/source/hvcgroep_nl.md) / rmn.nl
- [Reinis](/doc/source/ximmio_nl.md) / reinis.nl
- [Spaarne Landen](/doc/source/hvcgroep_nl.md) / spaarnelanden.nl
- [Stadswerk 072](/doc/source/hvcgroep_nl.md) / stadswerk072.nl
- [Twente Milieu](/doc/source/ximmio_nl.md) / twentemilieu.nl
- [Waardlanden](/doc/source/ximmio_nl.md) / waardlanden.nl
- [Ximmio](/doc/source/ximmio_nl.md) / ximmio.nl
- [ZRD](/doc/source/hvcgroep_nl.md) / zrd.nl
</details>

<details>
<summary>New Zealand</summary>

- [Auckland Council](/doc/source/aucklandcouncil_govt_nz.md) / aucklandcouncil.govt.nz
- [Christchurch City Council](/doc/source/ccc_govt_nz.md) / ccc.govt.nz
- [Gore, Invercargill & Southland](/doc/source/wastenet_org_nz.md) / wastenet.org.nz
- [Horowhenua District Council](/doc/source/horowhenua_govt_nz.md) / horowhenua.govt.nz
- [Waipa District Council](/doc/source/waipa_nz.md) / waipadc.govt.nz
- [Wellington City Council](/doc/source/wellington_govt_nz.md) / wellington.govt.nz
</details>

<details>
<summary>Norway</summary>

- [Min Renovasjon](/doc/source/minrenovasjon_no.md) / norkart.no
- [Oslo Kommune](/doc/source/oslokommune_no.md) / oslo.kommune.no
</details>

<details>
<summary>Poland</summary>

- [Ecoharmonogram](/doc/source/ecoharmonogram_pl.md) / ecoharmonogram.pl
- [Warsaw](/doc/source/warszawa19115_pl.md) / warszawa19115.pl
</details>

<details>
<summary>Sweden</summary>

- [Lerum Vatten och Avlopp](/doc/source/lerum_se.md) / vatjanst.lerum.se
- [Ronneby Miljöteknik](/doc/source/miljoteknik_se.md) / fyrfackronneby.se
- [SRV Återvinning](/doc/source/srvatervinning_se.md) / srvatervinning.se
- [SSAM](/doc/source/ssam_se.md) / ssam.se
- [Sysav Sophämntning](/doc/source/sysav_se.md) / sysav.se
- [VA Syd Sophämntning](/doc/source/vasyd_se.md) / vasyd.se
</details>

<details>
<summary>Switzerland</summary>

- [A-Region](/doc/source/a_region_ch.md) / a-region.ch
- [Andwil](/doc/source/a_region_ch.md) / a-region.ch
- [Appenzell](/doc/source/a_region_ch.md) / a-region.ch
- [Berg](/doc/source/a_region_ch.md) / a-region.ch
- [Bühler](/doc/source/a_region_ch.md) / a-region.ch
- [Eggersriet](/doc/source/a_region_ch.md) / a-region.ch
- [Gais](/doc/source/a_region_ch.md) / a-region.ch
- [Gaiserwald](/doc/source/a_region_ch.md) / a-region.ch
- [Goldach](/doc/source/a_region_ch.md) / a-region.ch
- [Grub](/doc/source/a_region_ch.md) / a-region.ch
- [Heiden](/doc/source/a_region_ch.md) / a-region.ch
- [Herisau](/doc/source/a_region_ch.md) / a-region.ch
- [Horn](/doc/source/a_region_ch.md) / a-region.ch
- [Hundwil](/doc/source/a_region_ch.md) / a-region.ch
- [Häggenschwil](/doc/source/a_region_ch.md) / a-region.ch
- [Lindau](/doc/source/lindau_ch.md) / lindau.ch
- [Lutzenberg](/doc/source/a_region_ch.md) / a-region.ch
- [Muolen](/doc/source/a_region_ch.md) / a-region.ch
- [Mörschwil](/doc/source/a_region_ch.md) / a-region.ch
- [Rehetobel](/doc/source/a_region_ch.md) / a-region.ch
- [Rorschach](/doc/source/a_region_ch.md) / a-region.ch
- [Rorschacherberg](/doc/source/a_region_ch.md) / a-region.ch
- [Schwellbrunn](/doc/source/a_region_ch.md) / a-region.ch
- [Schönengrund](/doc/source/a_region_ch.md) / a-region.ch
- [Speicher](/doc/source/a_region_ch.md) / a-region.ch
- [Stein](/doc/source/a_region_ch.md) / a-region.ch
- [Steinach](/doc/source/a_region_ch.md) / a-region.ch
- [Teufen](/doc/source/a_region_ch.md) / a-region.ch
- [Thal](/doc/source/a_region_ch.md) / a-region.ch
- [Trogen](/doc/source/a_region_ch.md) / a-region.ch
- [Tübach](/doc/source/a_region_ch.md) / a-region.ch
- [Untereggen](/doc/source/a_region_ch.md) / a-region.ch
- [Urnäsch](/doc/source/a_region_ch.md) / a-region.ch
- [Wald](/doc/source/a_region_ch.md) / a-region.ch
- [Waldkirch](/doc/source/a_region_ch.md) / a-region.ch
- [Waldstatt](/doc/source/a_region_ch.md) / a-region.ch
- [Wittenbach](/doc/source/a_region_ch.md) / a-region.ch
- [Wolfhalden](/doc/source/a_region_ch.md) / a-region.ch
</details>

<details>
<summary>United Kingdom</summary>

- [Ashfield District Council](/doc/source/ashfield_gov_uk.md) / ashfield.gov.uk
- [Bracknell Forest Council](/doc/source/bracknell_forest_gov_uk.md) / selfservice.mybfc.bracknell-forest.gov.uk
- [Bradford Metropolitan District Council](/doc/source/bradford_gov_uk.md) / bradford.gov.uk
- [Braintree District Council](/doc/source/braintree_gov_uk.md) / braintree.gov.uk
- [Breckland Council](/doc/source/breckland_gov_uk.md) / breckland.gov.uk/mybreckland
- [Cambridge City Council](/doc/source/cambridge_gov_uk.md) / cambridge.gov.uk
- [Canterbury City Council](/doc/source/canterbury_gov_uk.md) / canterbury.gov.uk
- [Cheshire East Council](/doc/source/cheshire_east_gov_uk.md) / cheshireeast.gov.uk
- [Chesterfield Borough Council](/doc/source/chesterfield_gov_uk.md) / chesterfield.gov.uk
- [City of York Council](/doc/source/york_gov_uk.md) / york.gov.uk
- [Colchester Borough Council](/doc/source/colchester_gov_uk.md) / colchester.gov.uk
- [Cornwall Council](/doc/source/cornwall_gov_uk.md) / cornwall.gov.uk
- [Derby City Council](/doc/source/derby_gov_uk.md) / derby.gov.uk
- [Eastbourne Borough Council](/doc/source/environmentfirst_co_uk.md) / lewes-eastbourne.gov.uk
- [Elmbridge Borough Council](/doc/source/elmbridge_gov_uk.md) / elmbridge.gov.uk
- [Environment First](/doc/source/environmentfirst_co_uk.md) / environmentfirst.co.uk
- [FCC Environment](/doc/source/fccenvironment_co_uk.md) / fccenvironment.co.uk
- [Guildford Borough Council](/doc/source/guildford_gov_uk.md) / guildford.gov.uk
- [Harborough District Council](/doc/source/fccenvironment_co_uk.md) / harborough.gov.uk
- [Horsham District Council](/doc/source/horsham_gov_uk.md) / horsham.gov.uk
- [Huntingdonshire District Council](/doc/source/huntingdonshire_gov_uk.md) / huntingdonshire.gov.uk
- [Lewes District Council](/doc/source/environmentfirst_co_uk.md) / lewes-eastbourne.gov.uk
- [London Borough of Lewisham](/doc/source/lewisham_gov_uk.md) / lewisham.gov.uk
- [Manchester City Council](/doc/source/manchester_uk.md) / manchester.gov.uk
- [Middlesbrough Council](/doc/source/middlesbrough_gov_uk.md) / middlesbrough.gov.uk
- [Newcastle City Council](/doc/source/newcastle_gov_uk.md) / community.newcastle.gov.uk
- [North Somerset Council](/doc/source/nsomerset_gov_uk.md) / n-somerset.gov.uk
- [Nottingham City Council](/doc/source/nottingham_city_gov_uk.md) / nottinghamcity.gov.uk
- [Peterborough City Council](/doc/source/peterborough_gov_uk.md) / peterborough.gov.uk
- [Richmondshire District Council](/doc/source/richmondshire_gov_uk.md) / richmondshire.gov.uk
- [Rushmoor Borough Council](/doc/source/rushmoor_gov_uk.md) / rushmoor.gov.uk
- [Salford City Council](/doc/source/salford_gov_uk.md) / salford.gov.uk
- [Sheffield City Council](/doc/source/sheffield_gov_uk.md) / sheffield.gov.uk
- [South Cambridgeshire District Council](/doc/source/scambs_gov_uk.md) / scambs.gov.uk
- [South Hams District Council](/doc/source/fccenvironment_co_uk.md) / southhams.gov.uk
- [South Norfolk and Broadland Council](/doc/source/south_norfolk_and_broadland_gov_uk.md) / area.southnorfolkandbroadland.gov.uk
- [Stevenage Borough Council](/doc/source/stevenage_gov_uk.md) / stevenage.gov.uk
- [Tewkesbury Borough Council](/doc/source/tewkesbury_gov_uk.md) / tewkesbury.gov.uk
- [The Royal Borough of Kingston Council](/doc/source/kingston_gov_uk.md) / kingston.gov.uk
- [Walsall Council](/doc/source/walsall_gov_uk.md) / walsall.gov.uk
- [West Berkshire Council](/doc/source/westberks_gov_uk.md) / westberks.gov.uk
- [West Devon Borough Council](/doc/source/fccenvironment_co_uk.md) / westdevon.gov.uk
- [Wiltshire Council](/doc/source/wiltshire_gov_uk.md) / wiltshire.gov.uk
</details>

<details>
<summary>United States of America</summary>

- [City of Pittsburgh](/doc/source/pgh_st.md) / pgh.st
- [Republic Services](/doc/source/republicservices_com.md) / republicservices.com
- [Seattle Public Utilities](/doc/source/seattle_gov.md) / myutilities.seattle.gov
</details>

<!--End of country section-->

---

# Installation and Configuration

![hacs badge](https://img.shields.io/badge/HACS-Default-orange)
![hacs installs](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fwaste_collection_schedule)

The Waste Collection Schedule can be installed via [HACS](https://hacs.xyz/), or by manually copying the [`waste_collection_schedule`](https://github.com/mampfes/hacs_waste_collection_schedule/tree/master/custom_components) directory to Home Assistant's `config/custom_components/` directory. For further details see the [installation and configuration](/doc/installation.md) page, or the [FAQ](/doc/faq.md).

# Contributing To The Project

![python badge](https://img.shields.io/badge/Made%20with-Python-orange)
![github contributors](https://img.shields.io/github/contributors/mampfes/hacs_waste_collection_schedule?color=orange)
![last commit](https://img.shields.io/github/last-commit/mampfes/hacs_waste_collection_schedule?color=orange)
[![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)](https://community.home-assistant.io/t/waste-collection-schedule-framework/186492)

There are several ways of contributing to this project, they include:

- Adding new service providers
- Updating or improving the documentation
- Helping answer/fix any issues raised
- Join in with the Home Assistant Community discussion

For further details see [contribution](/doc/contributing.md) guidelines, or take a look at our [online](/doc/online.md) mentions.

<!--
# Development Roadmap
The top 3 things on the development wish-list are:
- [ ] idea #1 - short description
- [ ] idea #2 - short description
- [ ] idea #3 - short description

If you'd like to help with any of these, please raise an [issue](https://github.com/mampfes/hacs_waste_collection_schedule/issues) indicating which item you'd like to work on.
-->

<!--
# Code of Conduct
 Not sure if this is relevant for this project.
-->

# Known Issues

The following waste service providers return errors when running the test_source script:

- `banyule_vic_gov_au`: JSONDecodeError, caused by not supported Captcha wall
- `awn_de`: all tests return 0 entries

If you can fix any of these, please raise a Pull Request with the updates.

---

## Home Assistant Hangs

**Problem:** Home Assistant hangs during restart or configuration check. This occurs typically after Waste Collection Schedule has been added to the configuration.

**Root Cause:** Home Assistant tries to install the required Python packages and fails somehow. This is not an issue of Waste Collection Schedule.

**Solution:** Try to reinstall Waste Collection Schedule (if you are using HACS) or install the required Python packages manually. This list of required packages can be found in [manifest.json](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/manifest.json#L5).

The actual procedure depends on your Home Assistant installation type.

Example:

```bash
sudo docker exec -it homeassistant /bin/bash
pip list
pip install recurring_ical_events  # in case recurring_ical_events is missing
```

# Licence

![github licence](https://img.shields.io/badge/Licence-MIT-orange)

This project uses the MIT Licence, for more details see the [licence](/doc/licence.md) document.

# Showing Your Appreciation

If you like this project, please give it a star on [GitHub](https://github.com/mampfes/hacs_waste_collection_schedule) or consider becoming a [Sponsor](https://github.com/sponsors/mampfes).

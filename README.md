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
<p>

- [Generic ICS / iCal File](/doc/source/ics.md)
- [User Specified](/doc/source/static.md)
</p>
</details>

<details>
<summary>Australia</summary>
<p>

- [Banyule City Council](/doc/source/banyule_vic_gov_au.md)
- [Belmont City Council](/doc/source/belmont_wa_gov_au.md)
- [Brisbane City Council](/doc/source/brisbane_qld_gov_au.md)
- [Campbelltown City Council](/doc/source/campbelltown_nsw_gov_au.md)
- [City of Canada Bay Council](/doc/source/canadabay_nsw_gov_au.md)
- [Inner West Council (NSW)](/doc/source/innerwest_nsw_gov_au.md)
- [Ku-ring-gai Council](/doc/source/kuringgai_nsw_gov_au.md)
- [Macedon Ranges Shire Council, Melbourne](/doc/source/mrsc_vic_gov_au.md)
- [Maroondah City Council](/doc/source/maroondah_vic_gov_au.md)
- [Melton City Council, Melbourne](/doc/source/melton_vic_gov_au.md)
- [Nillumbik Shire Council](/doc/source/nillumbik_vic_gov_au.md)
- [North Adelaide Waste Management Authority, South Australia](/doc/source/nawma_sa_gov_au.md)
- [RecycleSmart](/doc/source/recyclesmart_com.md)
- [Stonnington City Council, Melbourne](/doc/source/stonnington_vic_gov_au.md)
- [The Hills Council, Sydney](/doc/source/thehills_nsw_gov_au.md)
- [Wyndham City Council, Melbourne](/doc/source/wyndham_vic_gov_au.md)
</p>
</details>

<details>
<summary>Austria</summary>
<p>

- [BMV.at](/doc/source/bmv_at.md)
- [Data.Umweltprofis](/doc/source/data_umweltprofis_at.md)
- [Korneuburg Stadtservice](/doc/source/korneuburg_stadtservice_at.md)
- [WSZ-Moosburg.at](/doc/source/wsz_moosburg_at.md)
</p>
</details>

<details>
<summary>Belgium</summary>
<p>

- [Hygea.be](/doc/source/hygea_be.md)
- [Recycle! / RecycleApp.be](/doc/source/recycleapp_be.md)
</p>
</details>

<details>
<summary>Canada</summary>
<p>

- [City of Toronto](/doc/source/toronto_ca.md)
</p>
</details>

<details>
<summary>Germany</summary>
<p>

- [Abfall.IO / AbfallPlus.de](/doc/source/abfall_io.md)
- [AbfallNavi.de (RegioIT.de)](/doc/source/abfallnavi_de.md)
- [Abfallkalender Würzburg](/doc/source/wuerzburg_de.md)
- [Abfalltermine Forchheim](/doc/source/abfalltermine_forchheim_de.md)
- [Abfallwirtschaft Bremen](/doc/source/c_trace_de.md)
- [Abfallwirtschaft Landkreis Harburg](/doc/source/aw_harburg_de.md)
- [Abfallwirtschaft Landkreis Wolfenbüttel](/doc/source/alw_wf_de.md)
- [Abfallwirtschaft Neckar-Odenwald-Kreis](/doc/source/awn_de.md)
- [Abfallwirtschaft Rendsburg](/doc/source/awr_de.md)
- [Abfallwirtschaft Stuttgart](/doc/source/stuttgart_de.md)
- [Abfallwirtschaft Südholstein](/doc/source/awsh_de.md)
- [Abfallwirtschaft Zollernalbkreis](/doc/source/abfall_zollernalbkreis_de.md)
- [Alb-Donau-Kreis](/doc/source/buergerportal_de.md)
- [ART Trier](/doc/source/art_trier_de.md)
- [AWB Bad Kreuznach](/doc/source/awb_bad_kreuznach_de.md)
- [AWB Esslingen](/doc/source/awb_es_de.md)
- [AWB Landkreis Augsburg](/doc/source/c_trace_de.md)
- [AWB Limburg-Weilburg](/doc/source/awb_lm_de.md)
- [AWB Oldenburg](/doc/source/awb_oldenburg_de.md)
- [AWBKoeln.de](/doc/source/awbkoeln_de.md)
- [AWIDO-online.de](/doc/source/awido_de.md)
- [Berlin-Recycling.de](/doc/source/berlin_recycling_de.md)
- [Bogenschuetz-Entsorgung.de](/doc/source/infeo_at.md)
- [BSR.de / Berliner Stadtreinigungsbetriebe](/doc/source/bsr_de.md)
- [C-Trace.de](/doc/source/c_trace_de.md)
- [Cochem-Zell](/doc/source/cochem_zell_online_de.md)
- [EGN-Abfallkalender.de](/doc/source/egn_abfallkalender_de.md)
- [Erlangen-Höchstadt](/doc/source/erlangen_hoechstadt_de.md)
- [Jumomind.de](/doc/source/jumomind_de.md)
- [KAEV Niederlausitz](/doc/source/kaev_niederlausitz_de.md)
- [KWB-Goslar.de](/doc/source/kwb_goslar_de.md)
- [KWU-Entsorgung](/doc/source/kwu_de.md)
- [Landkreis-Wittmund.de](/doc/source/landkreis_wittmund_de.md)
- [Landkreis Rhön Grabfeld](/doc/source/landkreis_rhoen_grabfeld.md)
- [Landkreis Schwäbisch Hall](/doc/source/lrasha_de.md)
- [Muellmax.de](/doc/source/muellmax_de.md)
- [MyMuell App](/doc/source/jumomind_de.md)
- [Neunkirchen Siegerland](/doc/source/abfall_neunkirchen_siegerland_de.md)
- [RegioEntsorgung](/doc/source/regioentsorgung_de.md)
- [Rhein-Hunsrück Entsorgung (RHE)](/doc/source/rh_entsorgung_de.md)
- [Sector27.de](/doc/source/sector27_de.md)
- [Stadtreinigung Dresden](/doc/source/stadtreinigung_dresden_de.md)
- [Stadtreinigung.Hamburg](/doc/source/stadtreinigung_hamburg.md)
- [Stadtreinigung-Leipzig.de](/doc/source/stadtreinigung_leipzig_de.md)
- [Stadt-Willich.de](/doc/source/stadt_willich_de.md)
- [StadtService Brühl](/doc/source/stadtservice_bruehl_de.md)
- [Städteservice Raunheim Rüsselsheim](/doc/source/staedteservice_de.md)
- [Südbrandenburgischer Abfallzweckverband](/doc/source/sbazv_de.md)
- [Umweltbetrieb Stadt Bielefeld](/doc/source/bielefeld_de.md)
- [WAS Wolfsburg](/doc/source/was_wolfsburg_de.md)
- [Wermeldkirchen](/doc/source/wermelskirchen_de.md)
- [Zweckverband Abfallwirtschaft Werra-Meißner-Kreis](/doc/source/zva_wmk_de.md)

</p>
</details>

<details>
<summary>Lithuania</summary>
<p>

- [Kauno švara](/doc/source/grafikai_svara_lt.md)
</p>
</details>

<details>
<summary>Netherlands</summary>
<p>

- [HVCGroep and others](/doc/source/hvcgroep_nl.md)
- [Ximmio](/doc/source/ximmio_nl.md)
</p>
</details>

<details>
<summary>New Zealand</summary>
<p>

- [Auckland](/doc/source/aucklandcouncil_govt_nz.md)
- [Christchurch](/doc/source/ccc_govt_nz.md)
- [Gore, Invercargill & Southland](/doc/source/wastenet_org_nz.md)
- [Horowhenua District](/doc/source/horowhenua_govt_nz.md)
- [Waipa District](/doc/source/waipa_nz.md)
- [Wellington](/doc/source/wellington_govt_nz.md)
</p>
</details>

<details>
<summary>Norway</summary>
<p>

- [Min Renovasjon](/doc/source/minrenovasjon_no.md)
- [Oslo Kommune](/doc/source/oslokommune_no.md)
</p>
</details>

<details>
<summary>Poland</summary>
<p>

- [Warsaw](/doc/source/warszawa19115_pl.md)
- [Multiple communities - ecoharmonogram](/doc/source/ecoharmonogram_pl.md)
</p>
</details>

<details>
<summary>Sweden</summary>
<p>

- [Lerum.se](/doc/source/lerum_se.md)
- [Ronneby Miljöteknik](/doc/source/miljoteknik_se.md)
- [SSAM.se](/doc/source/ssam_se.md)
- [srvatervinning.se](/doc/source/srvatervinning_se.md)
- [Sysav.se](/doc/source/sysav_se.md)
- [Vasyd.se](/doc/source/vasyd_se.md)
</p>
</details>

<details>
<summary>Switzerland</summary>
<p>

- [A-Region.ch](/doc/source/a_region_ch.md)
- [Lindau.ch](/doc/source/lindau_ch.md)
</p>
</details>

<details>
<summary>United States of America</summary>
<p>

- [PGH.ST](/doc/source/pgh_st.md)
- [Republic Services](/doc/source/republicservices_com.md)
- [Seattle Public Utilities](/doc/source/seattle_gov.md)
</p>
</details>

<details>
<summary>United Kingdom</summary>
<p>

- [Bracknell Forest Council - bracknell-forest.gov.uk](/doc/source/bracknell_forest_gov_uk.md)
- [Bradford Metropolitan District Council - bradford.gov.uk](/doc/source/bradford_gov_uk.md)
- [Braintree District Council - braintree.gov.uk](/doc/source/braintree_gov_uk.md)
- [Cambridge City Council - cambridge.gov.uk](/doc/source/cambridge_gov_uk.md)
- [Canterbury City Council - canterbury.gov.uk](/doc/source/canterbury_gov_uk.md)
- [Cheshire East Council - cheshireeast.gov.uk](/doc/source/cheshire_east_gov_uk.md)
- [Chesterfield Borough Council - chesterfield.gov.uk](/doc/source/chesterfield_gov_uk.md)
- [Colchester Borough Council - colchester.gov.uk](/doc/source/colchester_gov_uk.md)
- [Cornwall Council - cornwall.gov.uk](/doc/source/cornwall_gov_uk.md)
- [Derby City Council - derby.gov.uk](/doc/source/derby_gov_uk.md)
- [Eastbourne Borough Council - lewes-eastbourne.gov.uk](/doc/source/environmentfirst_co_uk.md)
- [Elmbridge Borough Council - elmbridge.gov.uk](/doc/source/elmbridge_gov_uk.md)
- [Guildford Borough Council - guildford.gov.uk](/doc/source/guildford_gov_uk.md)
- [Harborough District Council - harborough.gov.uk](/doc/source/fccenvironment_co_uk.md)
- [Huntingdonshire District Council - huntingdonshire.gov.uk](/doc/source/huntingdonshire_gov_uk.md)
- [The Royal Borough of Kingston - kinston.gov.uk](/doc/source/kingston_gov_uk.md)
- [Lewes District Council - lewes-eastbourne.gov.uk](/doc/source/environmentfirst_co_uk.md)
- [London Borough of Lewisham - lewisham.gov.uk](.doc/source/lewisham_gov_uk.md)
- [Manchester City Council - manchester.gov.uk](/doc/source/manchester_uk.md)
- [Newcastle City Council - newcastle.gov.uk](/doc/source/newcastle_gov_uk.md)
- [North Somerset Council - n-somerset.gov.uk](/doc/source/nsomerset_gov_uk.md)
- [Nottingham City Council - nottinghamcity.gov.uk](/doc/source/nottingham_city_gov_uk.md)
- [Peterborough City Council - peterborough.gov.uk](/doc/source/peterborough_gov_uk.md)
- [Richmondshire District Council - richmondshire.gov.uk](/doc/source/richmondshire_gov_uk.md)
- [Rushmoor Borough Council - rushmoor.gov.uk](/doc/source/rushmoor_gov_uk.md)
- [Sheffield City Council - sheffield.gov.uk](/doc/source/sheffield_gov_uk.md)
- [South Cambridgeshire District Council - scambs.gov.uk](/doc/source/scambs_gov_uk.md)
- [South Norfolk and Broadland Council - southnorfolkandbroadland.gov.uk](/doc/source/south_norfolk_and_broadland_gov_uk.md)
- [Stevenage Borough Council - stevenage.gov.uk](/doc/source/stevenage_gov_uk.md)
- [Tewkwsbury Borough Council - tewkesbury.gov.uk](/doc/source/tewkesbury_gov_uk.md)
- [City of York Council - york.gov.uk](/doc/source/york_gov_uk.md)
- [Walsall Council - walsall.gov.uk](/doc/source/walsall_gov_uk.md)
- [West Berkshire Council - westberks.gov.uk](/doc/source/westberks_gov_uk.md)
- [Wiltshire Council - wiltshire.gov.uk](/doc/source/wiltshire_gov_uk.md)
</p>
</details>

# Installation and Configuration
![hacs badge](https://img.shields.io/badge/HACS-Default-orange)
![hacs installs](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fwaste_collection_schedule)

The Waste Collection Schedule can be installed via [HACS](https://hacs.xyz/), or by manually copying the [`waste_collection_schedule`](https://github.com/mampfes/hacs_waste_collection_schedule/tree/master/custom_components) directory to Home Assistant's `config/custom_components/` directory. For further details see the [installation and configuration](/doc/installation.md) page, or the [FAQ](/doc/faq.md).

# Contributing To The Project
![python badge](https://img.shields.io/badge/Made%20with-Python-orange)
![github contributors](https://img.shields.io/github/contributors/mampfes/hacs_waste_collection_schedule?color=orange)
![last commit](https://img.shields.io/github/last-commit/mampfes/hacs_waste_collection_schedule?color=orange)
![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)

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
The following waste service providers return errors when running the test_source script
- [ ] berlin_recycling_de, JSONDecodeError
- [ ] abfall_io, Traunstein test case fails
- [ ] sector27_de, TimeoutError
- [ ] banyule_vic_gov_au,  JSONDecodeError
- [ ] grafikai_svara_lt, TimeoutError
- [ ] warszawal9115_pl, HTTPError

If you can fix any of these, please raise a Pull Request with the updates.

# Licence
![github licence](https://img.shields.io/badge/Licence-MIT-orange)

This project uses the MIT Licence, for more details see the [licence](/doc/licence.md) document.

# Showing Your Appreciation
If you like this project, please give it a star on [GitHub](https://github.com/mampfes/hacs_waste_collection_schedule) or consider becomming a [Sponsor](https://github.com/sponsors/mampfes).

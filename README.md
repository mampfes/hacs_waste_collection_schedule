<!-- GitHub Markdown Reference: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github -->

<img src="https://raw.githubusercontent.com/mampfes/hacs_waste_collection_schedule/master/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Waste Collection Schedule

**A custom component for Home Assistant that retrieves waste collection schedules from a wide range of service providers.**

<img src="https://raw.githubusercontent.com/mampfes/hacs_waste_collection_schedule/master/images/wcs_animated.gif" alt="Waste Collection Schedule animation" title="Waste Collection Schedule" align="right" height="200" />

Waste collection schedules from service provider web sites are updated daily, derived from local ICS/iCal files, or generated from user-specified dates or regularly repeating date patterns. The Home Assistant built-in Calendar is automatically populated with schedules, and there is a high degree of flexibility in how information can be format and displayed in entity cards or pop-ups. The framework can easily be extended to support additional waste collection service providers, or other services which provide schedules.

# Supported Service Providers

Waste collection schedules in the following formats and countries are supported. Click on the section heading to view details of individual service providers.

If your service provider is not listed, feel free to open a [source request issue](https://github.com/mampfes/hacs_waste_collection_schedule/issues/new?assignees=&labels=source+request&projects=&template=SOURCE-REQUEST.yml&title=%5BSource+Request%5D%3A+) (please first check the [Issues section](https://github.com/mampfes/hacs_waste_collection_schedule/issues) if there already is an open issue for your service provider.).

<details>
<summary>ICS/iCal and User-Specified</summary>

- [Generic ICS / iCal File](/doc/source/ics.md)
- [User Specified](/doc/source/static.md)
- [Multiple Sources Wrapper](/doc/source/multiple.md)

</details>

<!--Begin of country section-->
<details>
<summary>Australia</summary>

- [Adelaide Hills Council](/doc/source/app_my_local_services_au.md) / ahc.sa.gov.au
- [Adelaide Plains Council](/doc/source/app_my_local_services_au.md) / apc.sa.gov.au
- [Alexandrina Council](/doc/source/app_my_local_services_au.md) / alexandrina.sa.gov.au
- [App Backend of My Local Services](/doc/source/app_my_local_services_au.md) / localcouncils.sa.gov.au
- [Armadale (Western Australia)](/doc/source/armadale_wa_gov_au.md) / armadale.wa.gov.au
- [Australian Capital Territory (ACT)](/doc/source/act_gov_au.md) / cityservices.act.gov.au/recycling-and-waste
- [Banyule City Council](/doc/source/banyule_vic_gov_au.md) / banyule.vic.gov.au
- [Baw Baw Shire Council](/doc/source/impactapps_com_au.md) / bawbawshire.vic.gov.au
- [Bayside City Council](/doc/source/impactapps_com_au.md) / bayside.vic.gov.au
- [Bega Valley Shire Council](/doc/source/impactapps_com_au.md) / begavalley.nsw.gov.au
- [Belmont City Council](/doc/source/belmont_wa_gov_au.md) / belmont.wa.gov.au
- [Berri Barmera Council](/doc/source/app_my_local_services_au.md) / berribarmera.sa.gov.au
- [Blacktown City Council (NSW)](/doc/source/blacktown_nsw_gov_au.md) / blacktown.nsw.gov.au
- [Blue Mountains City Council](/doc/source/impactapps_com_au.md) / bmcc.nsw.gov.au
- [Brisbane City Council](/doc/source/brisbane_qld_gov_au.md) / brisbane.qld.gov.au
- [Burwood City Council](/doc/source/impactapps_com_au.md) / burwood.nsw.gov.au
- [Campbelltown City Council](/doc/source/app_my_local_services_au.md) / campbelltown.sa.gov.au
- [Campbelltown City Council (NSW)](/doc/source/campbelltown_nsw_gov_au.md) / campbelltown.nsw.gov.au
- [Cardinia Shire Council](/doc/source/cardinia_vic_gov_au.md) / cardinia.vic.gov.au
- [City of Adelaide](/doc/source/app_my_local_services_au.md) / adelaidecitycouncil.com
- [City of Ballarat](/doc/source/ballarat_vic_gov_au.md) / ballarat.vic.gov.au
- [City of Burnside](/doc/source/app_my_local_services_au.md) / burnside.sa.gov.au
- [City of Canada Bay Council](/doc/source/canadabay_nsw_gov_au.md) / canadabay.nsw.gov.au
- [City of Charles Sturt](/doc/source/app_my_local_services_au.md) / charlessturt.sa.gov.au
- [City of Cockburn](/doc/source/cockburn_wa_gov_au.md) / cockburn.wa.gov.au
- [City of Darebin](/doc/source/darebin_vic_gov_au.md) / darebin.vic.gov.au
- [City of Greater Geelong](/doc/source/geelongaustralia_com_au.md) / geelongaustralia.com.au
- [City of Kingston](/doc/source/kingston_vic_gov_au.md) / kingston.vic.gov.au
- [City of Mitcham](/doc/source/app_my_local_services_au.md) / mitchamcouncil.sa.gov.au
- [City of Mount Gambier](/doc/source/app_my_local_services_au.md) / mountgambier.sa.gov.au
- [City of Norwood Payneham and St Peters](/doc/source/app_my_local_services_au.md) / npsp.sa.gov.au
- [City of Onkaparinga](/doc/source/app_my_local_services_au.md) / onkaparingacity.com
- [City of Onkaparinga Council](/doc/source/onkaparingacity_com.md) / onkaparingacity.com
- [City of Port Adelaide Enfield](/doc/source/app_my_local_services_au.md) / cityofpae.sa.gov.au
- [City of Prospect](/doc/source/app_my_local_services_au.md) / prospect.sa.gov.au
- [City of Ryde (NSW)](/doc/source/ryde_nsw_gov_au.md) / ryde.nsw.gov.au
- [City of Salisbury](/doc/source/app_my_local_services_au.md) / salisbury.sa.gov.au
- [City of Wanneroo](/doc/source/wanneroo_wa_gov_au.md) / wanneroo.wa.gov.au
- [City of West Torrens](/doc/source/app_my_local_services_au.md) / westtorrens.sa.gov.au
- [City of Whyalla](/doc/source/app_my_local_services_au.md) / whyalla.sa.gov.au
- [Clare and Gilbert Valleys Council](/doc/source/app_my_local_services_au.md) / claregilbertvalleys.sa.gov.au
- [Coorong District Council](/doc/source/app_my_local_services_au.md) / coorong.sa.gov.au
- [Council of Copper Coast](/doc/source/app_my_local_services_au.md) / coppercoast.sa.gov.au
- [Cowra Council](/doc/source/impactapps_com_au.md) / cowracouncil.com.au
- [Cumberland Council (NSW)](/doc/source/cumberland_nsw_gov_au.md) / cumberland.nsw.gov.au
- [District Council of Barunga West](/doc/source/app_my_local_services_au.md) / barungawest.sa.gov.au
- [District Council of Ceduna](/doc/source/app_my_local_services_au.md) / ceduna.sa.gov.au
- [District Council of Cleve](/doc/source/app_my_local_services_au.md) / cleve.sa.gov.au
- [District Council of Elliston](/doc/source/app_my_local_services_au.md) / elliston.sa.gov.au
- [District Council of Loxton Waikerie](/doc/source/app_my_local_services_au.md) / loxtonwaikerie.sa.gov.au
- [District Council of Mount Barker](/doc/source/app_my_local_services_au.md) / mountbarker.sa.gov.au
- [District Council of Mount Remarkable](/doc/source/app_my_local_services_au.md) / mtr.sa.gov.au
- [District Council of Robe](/doc/source/app_my_local_services_au.md) / robe.sa.gov.au
- [District Council of Streaky Bay](/doc/source/app_my_local_services_au.md) / streakybay.sa.gov.au
- [Forbes Shire Council](/doc/source/impactapps_com_au.md) / forbes.nsw.gov.au
- [Frankston City Council](/doc/source/frankston_vic_gov_au.md) / frankston.gov.au
- [Gold Coast City Council](/doc/source/goldcoast_qld_gov_au.md) / goldcoast.qld.gov.au
- [Gwydir Shire Council](/doc/source/impactapps_com_au.md) / gwydir.nsw.gov.au
- [Hobsons Bay City Council](/doc/source/hobsonsbay_vic_gov_au.md) / hobsonsbay.vic.gov.au
- [Hornsby Shire Council](/doc/source/hornsby_nsw_gov_au.md) / hornsby.nsw.gov.au
- [Hume City Council](/doc/source/hume_vic_gov_au.md) / hume.vic.gov.au
- [Impact Apps](/doc/source/impactapps_com_au.md) / impactapps.com.au
- [Inner West Council (NSW)](/doc/source/innerwest_nsw_gov_au.md) / innerwest.nsw.gov.au
- [Ipswich City Council](/doc/source/ipswich_qld_gov_au.md) / ipswich.qld.gov.au
- [Knox City Council](/doc/source/knox_vic_gov_au.md) / knox.vic.gov.au
- [Ku-ring-gai Council](/doc/source/kuringgai_nsw_gov_au.md) / krg.nsw.gov.au
- [Lake Macquarie City Council](/doc/source/lakemac_nsw_gov_au.md) / lakemac.com.au
- [Light Regional Council](/doc/source/app_my_local_services_au.md) / light.sa.gov.au
- [Lithgow City Council](/doc/source/impactapps_com_au.md) / lithgow.nsw.gov.au
- [Livingstone Shire Council](/doc/source/impactapps_com_au.md) / livingstone.qld.gov.au
- [Loddon Shire Council](/doc/source/impactapps_com_au.md) / loddon.vic.gov.au
- [Logan City Council](/doc/source/logan_qld_gov_au.md) / logan.qld.gov.au
- [Macedon Ranges Shire Council](/doc/source/mrsc_vic_gov_au.md) / mrsc.vic.gov.au
- [Mansfield Shire Council](/doc/source/mansfield_vic_gov_au.md) / mansfield.vic.gov.au
- [Maribyrnong Council](/doc/source/maribyrnong_vic_gov_au.md) / maribyrnong.vic.gov.au/Residents/Bins-and-recycling
- [Maroondah City Council](/doc/source/maroondah_vic_gov_au.md) / maroondah.vic.gov.au
- [Melton City Council](/doc/source/melton_vic_gov_au.md) / melton.vic.gov.au
- [Merri-bek City Council](/doc/source/merri_bek_vic_gov_au.md) / merri-bek.vic.gov.au
- [Mid Murray Council](/doc/source/app_my_local_services_au.md) / mid-murray.sa.gov.au
- [Moira Shire Council](/doc/source/impactapps_com_au.md) / moira.vic.gov.au
- [Moree Plains Shire Council](/doc/source/impactapps_com_au.md) / mpsc.nsw.gov.au
- [Moreton Bay](/doc/ics/moretonbay_qld_gov_au.md) / moretonbay.qld.gov.au
- [Mosman Council](/doc/source/mosman_nsw_gov_au.md) / mosman.nsw.gov.au
- [Naracoorte Lucindale Council](/doc/source/app_my_local_services_au.md) / naracoortelucindale.sa.gov.au
- [Nillumbik Shire Council](/doc/source/nillumbik_vic_gov_au.md) / nillumbik.vic.gov.au
- [North Adelaide Waste Management Authority](/doc/source/nawma_sa_gov_au.md) / nawma.sa.gov.au
- [Northern Areas Council](/doc/source/app_my_local_services_au.md) / nacouncil.sa.gov.au/page.aspx
- [Penrith City Council](/doc/source/impactapps_com_au.md) / penrithcity.nsw.gov.au
- [Port Adelaide Enfield, South Australia](/doc/source/portenf_sa_gov_au.md) / ecouncil.portenf.sa.gov.au
- [Port Augusta City Council](/doc/source/app_my_local_services_au.md) / portaugusta.sa.gov.au
- [Port Macquarie Hastings Council](/doc/source/impactapps_com_au.md) / pmhc.nsw.gov.au
- [Port Pirie Regional Council](/doc/source/app_my_local_services_au.md) / pirie.sa.gov.au
- [Port Stephens Council](/doc/source/portstephens_nsw_gov_au.md) / portstephens.nsw.gov.au
- [Queanbeyan-Palerang Regional Council](/doc/source/impactapps_com_au.md) / qprc.nsw.gov.au
- [RecycleSmart](/doc/source/recyclesmart_com.md) / recyclesmart.com
- [Redland City Council (QLD)](/doc/source/redland_qld_gov_au.md) / redland.qld.gov.au
- [Regional Council of Goyder](/doc/source/app_my_local_services_au.md) / goyder.sa.gov.au
- [Renmark Paringa Council](/doc/source/app_my_local_services_au.md) / renmarkparinga.sa.gov.au
- [Rural City of Murray Bridge](/doc/source/app_my_local_services_au.md) / murraybridge.sa.gov.au
- [Shellharbour City Council](/doc/source/shellharbourwaste_com_au.md) / shellharbourwaste.com.au
- [Singleton Council](/doc/source/impactapps_com_au.md) / singleton.nsw.gov.au
- [Snowy Valleys Council](/doc/source/impactapps_com_au.md) / snowyvalleys.nsw.gov.au
- [South Burnett Regional Council](/doc/source/impactapps_com_au.md) / southburnett.qld.gov.au
- [Southern Mallee District Council](/doc/source/app_my_local_services_au.md) / southernmallee.sa.gov.au
- [Stirling](/doc/source/stirling_wa_gov_au.md) / stirling.wa.gov.au
- [Stonnington City Council](/doc/source/stonnington_vic_gov_au.md) / stonnington.vic.gov.au
- [The Flinders Ranges Council](/doc/source/app_my_local_services_au.md) / frc.sa.gov.au/page.aspx
- [The Hawkesbury City Council, Sydney](/doc/source/hawkesbury_nsw_gov_au.md) / hawkesbury.nsw.gov.au
- [The Hills Shire Council, Sydney](/doc/source/thehills_nsw_gov_au.md) / thehills.nsw.gov.au
- [Town of Victoria Park](/doc/source/victoriapark_wa_gov_au.md) / victoriapark.wa.gov.au
- [Town of Walkerville](/doc/source/app_my_local_services_au.md) / walkerville.sa.gov.au
- [Townsville](/doc/source/townsville_qld_gov_au.md) / townsville.qld.gov.au
- [Unley City Council (SA)](/doc/source/unley_sa_gov_au.md) / unley.sa.gov.au
- [Wakefield Regional Council](/doc/source/app_my_local_services_au.md) / wakefieldrc.sa.gov.au
- [Wellington Shire Council](/doc/source/impactapps_com_au.md) / wellington.vic.gov.au
- [Whitehorse City Counfil](/doc/source/whitehorse_vic_gov_au.md) / whitehorse.vic.gov.au
- [Whittlesea City Council](/doc/source/whittlesea_vic_gov_au.md) / whittlesea.vic.gov.au/My-Neighbourhood
- [Wollondilly Shire Council](/doc/source/wollondilly_nsw_gov_au.md) / wollondilly.nsw.gov.au
- [Wollongong City Council](/doc/source/wollongongwaste_com_au.md) / wollongongwaste.com
- [Wyndham City Council, Melbourne](/doc/source/wyndham_vic_gov_au.md) / wyndham.vic.gov.au
- [Yankalilla District Council](/doc/source/app_my_local_services_au.md) / yankalilla.sa.gov.au
- [Yarra Ranges Council](/doc/source/yarra_ranges_vic_gov_au.md) / yarraranges.vic.gov.au
- [Yorke Peninsula Council](/doc/source/app_my_local_services_au.md) / yorke.sa.gov.au
</details>

<details>
<summary>Austria</summary>

- [Abfallverband Hollabrunn](/doc/source/umweltverbaende_at.md) / hollabrunn.umweltverbaende.at
- [Abfallverband Korneuburg](/doc/source/umweltverbaende_at.md) / korneuburg.umweltverbaende.at
- [Abfallverband Schwechat](/doc/source/umweltverbaende_at.md) / schwechat.umweltverbaende.at
- [Abfallwirtschaft der Stadt St. Pölten](/doc/ics/st-poelten_at.md) / st-poelten.at/sonstiges/17653-abfallkalender
- [Abfallwirtschaft Stadt Krems](/doc/source/umweltverbaende_at.md) / kremsstadt.umweltverbaende.at
- [Absdorf](/doc/source/citiesapps_com.md) / absdorf.gv.at
- [Afritz am See](/doc/ics/muellapp_com.md) / muellapp.com
- [Alpbach](/doc/ics/muellapp_com.md) / muellapp.com
- [Altenmarkt an der Triesting](/doc/source/citiesapps_com.md) / altenmarkt-triesting.gv.at
- [Althofen](/doc/ics/muellapp_com.md) / muellapp.com
- [Andau](/doc/source/citiesapps_com.md) / andau-gemeinde.at
- [Andrichsfurt](/doc/source/citiesapps_com.md) / andrichsfurt.at
- [Angath](/doc/ics/muellapp_com.md) / muellapp.com
- [Apetlon](/doc/source/citiesapps_com.md) / gemeinde-apetlon.at
- [App CITIES](/doc/source/citiesapps_com.md) / citiesapps.com
- [Arnoldstein](/doc/ics/muellapp_com.md) / muellapp.com
- [Aschau im Zillertal](/doc/ics/muellapp_com.md) / muellapp.com
- [AWV Neunkirchen](/doc/source/umweltverbaende_at.md) / neunkirchen.umweltverbaende.at
- [AWV Wr. Neustadt](/doc/source/umweltverbaende_at.md) / wrneustadt.umweltverbaende.at
- [Bad Blumau](/doc/source/citiesapps_com.md) / bad-blumau-gemeinde.at
- [Bad Fischau-Brunn](/doc/source/citiesapps_com.md) / bad-fischau-brunn.at
- [Bad Gleichenberg](/doc/source/citiesapps_com.md) / bad-gleichenberg.gv.at
- [Bad Häring](/doc/ics/muellapp_com.md) / muellapp.com
- [Bad Kleinkirchheim](/doc/ics/muellapp_com.md) / muellapp.com
- [Bad Loipersdorf](/doc/source/citiesapps_com.md) / gemeinde.loipersdorf.at
- [Bad Radkersburg](/doc/source/citiesapps_com.md) / bad-radkersburg.gv.at
- [Bad Schallerbach](/doc/source/citiesapps_com.md) / bad-schallerbach.at
- [Bad Tatzmannsdorf](/doc/source/citiesapps_com.md) / bad-tatzmannsdorf.at
- [Bad Waltersdorf](/doc/source/citiesapps_com.md) / bad-waltersdorf.gv.at/home
- [Baldramsdorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Behamberg](/doc/source/citiesapps_com.md) / behamberg.gv.at
- [Berg im Drautal](/doc/ics/muellapp_com.md) / muellapp.com
- [Berndorf bei Salzburg](/doc/ics/muellapp_com.md) / muellapp.com
- [Bernstein](/doc/source/citiesapps_com.md) / bernstein.gv.at
- [Bildein](/doc/source/citiesapps_com.md) / bildein.at
- [Birkfeld](/doc/source/citiesapps_com.md) / birkfeld.at
- [Blindenmarkt](/doc/source/citiesapps_com.md) / blindenmarkt.gv.at
- [Brandenberg](/doc/ics/muellapp_com.md) / muellapp.com
- [Breitenbach am Inn](/doc/ics/muellapp_com.md) / muellapp.com
- [Breitenbrunn am Neusiedler See](/doc/source/citiesapps_com.md) / breitenbrunn.at
- [Breitenstein](/doc/source/citiesapps_com.md) / breitenstein.at
- [Bromberg](/doc/source/citiesapps_com.md) / bromberg.at
- [Bruckneudorf](/doc/source/citiesapps_com.md) / bruckneudorf.eu
- [Buch - St. Magdalena](/doc/source/citiesapps_com.md) / buch-stmagdalena.at
- [Burgau](/doc/source/citiesapps_com.md) / burgau.info
- [Burgauberg-Neudauberg](/doc/source/citiesapps_com.md) / burgauberg-neudauberg.at
- [Burgenländischer Müllverband](/doc/source/bmv_at.md) / bmv.at
- [Burgschleinitz-Kühnring](/doc/source/citiesapps_com.md) / burgschleinitz-kuehnring.at
- [Bürg-Vöstenhof](/doc/source/citiesapps_com.md) / buerg-voestenhof.at
- [Dechantskirchen](/doc/source/citiesapps_com.md) / dechantskirchen.gv.at
- [Dellach](/doc/ics/muellapp_com.md) / muellapp.com
- [Dellach im Drautal](/doc/ics/muellapp_com.md) / muellapp.com
- [Deutsch Goritz](/doc/source/citiesapps_com.md) / deutsch-goritz.at
- [Deutsch Jahrndorf](/doc/source/citiesapps_com.md) / deutsch-jahrndorf.at
- [Deutsch Kaltenbrunn](/doc/source/citiesapps_com.md) / deutschkaltenbrunn.eu
- [Deutschkreutz](/doc/source/citiesapps_com.md) / deutschkreutz.at
- [Die NÖ Umweltverbände](/doc/source/umweltverbaende_at.md) / umweltverbaende.at
- [Dobl-Zwaring](/doc/source/citiesapps_com.md) / dobl-zwaring.gv.at
- [Drasenhofen](/doc/source/citiesapps_com.md) / drasenhofen.at
- [Draßmarkt](/doc/source/citiesapps_com.md) / drassmarkt.at
- [Ebenthal in Kärnten](/doc/ics/muellapp_com.md) / muellapp.com
- [Eberau](/doc/source/citiesapps_com.md) / eberau.riskommunal.net
- [Eberndorf](/doc/source/citiesapps_com.md) / eberndorf.at
- [Ebersdorf](/doc/source/citiesapps_com.md) / ebersdorf.eu
- [Eberstein](/doc/source/citiesapps_com.md) / eberstein.at
- [Edelsbach bei Feldbach](/doc/source/citiesapps_com.md) / edelsbach.at
- [Eggenburg](/doc/source/citiesapps_com.md) / eggenburg.gv.at
- [Eggersdorf bei Graz](/doc/source/citiesapps_com.md) / eggersdorf-graz.gv.at
- [Eichgraben](/doc/source/citiesapps_com.md) / eichgraben.at
- [Eisenstadt](/doc/source/citiesapps_com.md) / eisenstadt.gv.at
- [Enzenreith](/doc/source/citiesapps_com.md) / gemeinde-enzenreith.at
- [Eugendorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Fehring](/doc/source/citiesapps_com.md) / fehring.at
- [Feistritz im Rosental](/doc/ics/muellapp_com.md) / muellapp.com
- [Feistritz ob Bleiburg](/doc/source/citiesapps_com.md) / feistritz-bleiburg.gv.at
- [Feistritztal](/doc/source/citiesapps_com.md) / feistritztal.at
- [Feldbach](/doc/source/citiesapps_com.md) / feldbach.gv.at
- [Feldkirchen in Kärnten](/doc/source/citiesapps_com.md) / feldkirchen.at
- [Feldkirchen in Kärnten](/doc/ics/muellapp_com.md) / muellapp.com
- [Ferlach](/doc/ics/muellapp_com.md) / muellapp.com
- [Ferndorf](/doc/source/citiesapps_com.md) / ferndorf.gv.at
- [Ferndorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Finkenstein am Faaker See](/doc/ics/muellapp_com.md) / muellapp.com
- [Frankenau-Unterpullendorf](/doc/source/citiesapps_com.md) / frankenau-unterpullendorf.gv.at
- [Frankenfels](/doc/source/citiesapps_com.md) / frankenfels.at
- [Frauenkirchen](/doc/source/citiesapps_com.md) / frauenkirchen.at
- [Frauenstein](/doc/ics/muellapp_com.md) / muellapp.com
- [Freistadt](/doc/source/citiesapps_com.md) / freistadt.at
- [Fresach](/doc/source/citiesapps_com.md) / fresach.gv.at
- [Friedberg](/doc/source/citiesapps_com.md) / friedberg.gv.at
- [Frohnleiten](/doc/source/citiesapps_com.md) / frohnleiten.com
- [Fürstenfeld](/doc/source/citiesapps_com.md) / fuerstenfeld.gv.at
- [Gabersdorf](/doc/source/citiesapps_com.md) / gabersdorf.gv.at
- [GABL](/doc/source/umweltverbaende_at.md) / bruck.umweltverbaende.at
- [Gattendorf](/doc/source/citiesapps_com.md) / gattendorf.at
- [GAUL Laa an der Thaya](/doc/source/umweltverbaende_at.md) / laa.umweltverbaende.at
- [GAUM Mistelbach](/doc/source/umweltverbaende_at.md) / mistelbach.umweltverbaende.at
- [GDA Amstetten](/doc/ics/gda_gv_at.md) / gda.gv.at
- [Gemeindeverband Horn](/doc/source/umweltverbaende_at.md) / horn.umweltverbaende.at
- [Gersdorf an der Feistritz](/doc/source/citiesapps_com.md) / gersdorf.gv.at
- [Gitschtal](/doc/source/citiesapps_com.md) / gitschtal.gv.at
- [Gitschtal](/doc/ics/muellapp_com.md) / muellapp.com
- [Globasnitz](/doc/ics/muellapp_com.md) / muellapp.com
- [Gmünd in Kärnten](/doc/ics/muellapp_com.md) / muellapp.com
- [Gols](/doc/source/citiesapps_com.md) / gols.at
- [Grafendorf bei Hartberg](/doc/source/citiesapps_com.md) / grafendorf.at
- [Grafenschachen](/doc/source/citiesapps_com.md) / grafenschachen.at
- [Grafenstein](/doc/source/citiesapps_com.md) / grafenstein.gv.at
- [Grafenstein](/doc/ics/muellapp_com.md) / muellapp.com
- [Gratkorn](/doc/source/citiesapps_com.md) / gratkorn.gv.at
- [Gratwein-Straßengel](/doc/source/citiesapps_com.md) / gratwein-strassengel.gv.at
- [Greifenburg](/doc/ics/muellapp_com.md) / muellapp.com
- [Großkirchheim](/doc/ics/muellapp_com.md) / muellapp.com
- [Großsteinbach](/doc/source/citiesapps_com.md) / gemeinde-grosssteinbach.at
- [Großwarasdorf](/doc/source/citiesapps_com.md) / grosswarasdorf.at
- [Großwilfersdorf](/doc/source/citiesapps_com.md) / grosswilfersdorf.steiermark.at
- [Grödig](/doc/source/citiesapps_com.md) / groedig.at
- [Gutenberg](/doc/source/citiesapps_com.md) / gutenberg-stenzengreith.gv.at
- [Guttaring](/doc/ics/muellapp_com.md) / muellapp.com
- [GV Gmünd](/doc/source/umweltverbaende_at.md) / gmuend.umweltverbaende.at
- [GV Krems](/doc/source/umweltverbaende_at.md) / krems.umweltverbaende.at
- [GV Zwettl](/doc/source/umweltverbaende_at.md) / zwettl.umweltverbaende.at
- [GVA Baden](/doc/source/baden_umweltverbaende_at.md) / baden.umweltverbaende.at
- [GVA Baden](/doc/source/umweltverbaende_at.md) / baden.umweltverbaende.at
- [GVA Lilienfeld](/doc/source/umweltverbaende_at.md) / lilienfeld.umweltverbaende.at
- [GVA Mödling](/doc/source/umweltverbaende_at.md) / moedling.umweltverbaende.at
- [GVA Tulln](/doc/source/umweltverbaende_at.md) / tulln.umweltverbaende.at
- [GVA Waidhofen/Thaya](/doc/source/umweltverbaende_at.md) / waidhofen.umweltverbaende.at
- [GVU Bezirk Gänserndorf](/doc/source/umweltverbaende_at.md) / gaenserndorf.umweltverbaende.at
- [GVU Melk](/doc/source/umweltverbaende_at.md) / melk.umweltverbaende.at
- [GVU Scheibbs](/doc/source/scheibbs_umweltverbaende_at.md) / scheibbs.umweltverbaende.at
- [GVU Scheibbs](/doc/source/umweltverbaende_at.md) / scheibbs.umweltverbaende.at
- [GVU St. Pölten](/doc/source/umweltverbaende_at.md) / stpoeltenland.umweltverbaende.at
- [Güssing](/doc/source/citiesapps_com.md) / guessing.co.at
- [Güttenbach](/doc/source/citiesapps_com.md) / guettenbach.at
- [Haag am Hausruck](/doc/source/citiesapps_com.md) / haag-hausruck.at
- [Hagenberg im Mühlkreis](/doc/source/citiesapps_com.md) / hagenberg.at
- [Hannersdorf](/doc/source/citiesapps_com.md) / hannersdorf.at
- [Hartberg](/doc/source/citiesapps_com.md) / hartberg.at
- [Heiligenblut am Großglockner](/doc/ics/muellapp_com.md) / muellapp.com
- [Heiligenkreuz](/doc/source/citiesapps_com.md) / heiligenkreuz.at
- [Heiligenkreuz am Waasen](/doc/source/citiesapps_com.md) / heiligenkreuz-waasen.gv.at
- [Heimschuh](/doc/source/citiesapps_com.md) / heimschuh.at
- [Heldenberg](/doc/source/citiesapps_com.md) / heldenberg.gv.at
- [Henndorf am Wallersee](/doc/source/citiesapps_com.md) / henndorf.at
- [Henndorf am Wallersee](/doc/ics/muellapp_com.md) / muellapp.com
- [Hermagor-Pressegger See](/doc/ics/muellapp_com.md) / muellapp.com
- [Heugraben](/doc/source/citiesapps_com.md) / heugraben.at
- [Hirm](/doc/source/citiesapps_com.md) / hirm.gv.at
- [Hofstätten an der Raab](/doc/source/citiesapps_com.md) / hofstaetten.at
- [Hopfgarten im Brixental](/doc/ics/muellapp_com.md) / muellapp.com
- [Horitschon](/doc/source/citiesapps_com.md) / horitschon.at
- [Horn](/doc/source/citiesapps_com.md) / horn.gv.at
- [Hornstein](/doc/source/citiesapps_com.md) / hornstein.at
- [Hüttenberg](/doc/source/citiesapps_com.md) / huettenberg.at
- [Ilz](/doc/source/citiesapps_com.md) / ilz.at
- [Ilztal](/doc/source/citiesapps_com.md) / ilztal.at
- [infeo](/doc/source/infeo_at.md) / infeo.at
- [Innsbrucker Kommunalbetriebe](/doc/source/infeo_at.md) / ikb.at
- [Inzenhof](/doc/source/citiesapps_com.md) / inzenhof.at
- [Irschen](/doc/ics/muellapp_com.md) / muellapp.com
- [Jabing](/doc/source/citiesapps_com.md) / gemeinde-jabing.at
- [Jagerberg](/doc/source/citiesapps_com.md) / jagerberg.info
- [Kaindorf](/doc/source/citiesapps_com.md) / kaindorf.at
- [Kaisersdorf](/doc/source/citiesapps_com.md) / kaisersdorf.com
- [Kalsdorf bei Graz](/doc/source/citiesapps_com.md) / kalsdorf-graz.gv.at
- [Kapfenstein](/doc/source/citiesapps_com.md) / kapfenstein.at
- [Kemeten](/doc/source/citiesapps_com.md) / kemeten.gv.at
- [Keutschach am See](/doc/ics/muellapp_com.md) / muellapp.com
- [Kirchbach](/doc/ics/muellapp_com.md) / muellapp.com
- [Kirchbach-Zerlach](/doc/source/citiesapps_com.md) / kirchbach-zerlach.at
- [Kirchberg an der Raab](/doc/source/citiesapps_com.md) / kirchberg-raab.gv.at
- [Kirchbichl](/doc/ics/muellapp_com.md) / muellapp.com
- [Kirchdorf in Tirol](/doc/ics/muellapp_com.md) / muellapp.com
- [Kittsee](/doc/source/citiesapps_com.md) / kittsee.at
- [Klagenfurt am Wörthersee](/doc/ics/muellapp_com.md) / muellapp.com
- [Kleblach-Lind](/doc/ics/muellapp_com.md) / muellapp.com
- [Kleinmürbisch](/doc/source/citiesapps_com.md) / kleinmürbisch.at
- [Klingenbach](/doc/source/citiesapps_com.md) / klingenbach.at
- [Klosterneuburg](/doc/source/umweltverbaende_at.md) / klosterneuburg.umweltverbaende.at
- [Klöch](/doc/source/citiesapps_com.md) / kloech.com
- [Kobersdorf](/doc/source/citiesapps_com.md) / kobersdorf.at/index.php
- [Kohfidisch](/doc/source/citiesapps_com.md) / kohfidisch.at
- [Korneuburg](/doc/source/citiesapps_com.md) / korneuburg.gv.at
- [Krems in Kärnten](/doc/ics/muellapp_com.md) / muellapp.com
- [Krensdorf](/doc/source/citiesapps_com.md) / krensdorf.at
- [Krumpendorf am Wörthersee](/doc/ics/muellapp_com.md) / muellapp.com
- [Kuchl](/doc/source/citiesapps_com.md) / kuchl.net
- [Kundl](/doc/ics/muellapp_com.md) / muellapp.com
- [Kössen](/doc/ics/muellapp_com.md) / muellapp.com
- [Köstendorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Kötschach-Mauthen](/doc/source/citiesapps_com.md) / koetschach-mauthen.gv.at
- [Kötschach-Mauthen](/doc/ics/muellapp_com.md) / muellapp.com
- [Köttmannsdorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Laa an der Thaya](/doc/source/citiesapps_com.md) / laa.at
- [Lackenbach](/doc/source/citiesapps_com.md) / gemeinde-lackenbach.at
- [Lackendorf](/doc/source/citiesapps_com.md) / lackendorf.at
- [Langau](/doc/source/citiesapps_com.md) / langau.at
- [Langenrohr](/doc/source/citiesapps_com.md) / langenrohr.gv.at
- [Langenzersdorf](/doc/source/citiesapps_com.md) / langenzersdorf.gv.at
- [Leibnitz](/doc/source/citiesapps_com.md) / leibnitz.at
- [Leithaprodersdorf](/doc/source/citiesapps_com.md) / leithaprodersdorf.at
- [Lendorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Leoben](/doc/ics/muellapp_com.md) / muellapp.com
- [Lesachtal](/doc/ics/muellapp_com.md) / muellapp.com
- [Leutschach an der Weinstraße](/doc/source/citiesapps_com.md) / leutschach-weinstrasse.gv.at
- [Lieboch](/doc/source/citiesapps_com.md) / lieboch.gv.at
- [Linz AG](/doc/ics/linzag_at.md) / linzag.at
- [Litzelsdorf](/doc/source/citiesapps_com.md) / litzelsdorf.at
- [Loipersbach im Burgenland](/doc/source/citiesapps_com.md) / loipersbach.info
- [Ludersdorf - Wilfersdorf](/doc/source/citiesapps_com.md) / lu-wi.at
- [Ludmannsdorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Lurnfeld](/doc/ics/muellapp_com.md) / muellapp.com
- [Magdalensberg](/doc/ics/muellapp_com.md) / muellapp.com
- [Mallnitz](/doc/ics/muellapp_com.md) / muellapp.com
- [Malta](/doc/ics/muellapp_com.md) / muellapp.com
- [Maria Rain](/doc/ics/muellapp_com.md) / muellapp.com
- [Maria Saal](/doc/ics/muellapp_com.md) / muellapp.com
- [Maria Wörth](/doc/ics/muellapp_com.md) / muellapp.com
- [Mariasdorf](/doc/source/citiesapps_com.md) / mariasdorf.at
- [Markt Allhau](/doc/source/citiesapps_com.md) / marktallhau.gv.at
- [Markt Hartmannsdorf](/doc/source/citiesapps_com.md) / markthartmannsdorf.at
- [Markt Neuhodis](/doc/source/citiesapps_com.md) / markt-neuhodis.at
- [Markt Piesting Dreistetten](/doc/ics/piesting_at.md) / piesting.at
- [Markt Piesting-Dreistetten](/doc/source/citiesapps_com.md) / piesting.at
- [Marktgemeinde Edlitz](/doc/source/edlitz_at.md) / edlitz.at
- [Marktgemeinde Lockenhaus](/doc/source/citiesapps_com.md) / lockenhaus.at
- [Marz](/doc/source/citiesapps_com.md) / marz.gv.at
- [Mattersburg](/doc/source/citiesapps_com.md) / mattersburg.gv.at
- [Mattsee](/doc/ics/muellapp_com.md) / muellapp.com
- [Mayer Recycling](/doc/ics/mayer_recycling_at.md) / mayer-recycling.at
- [Meiseldorf](/doc/source/citiesapps_com.md) / meiseldorf.gv.at
- [Melk](/doc/source/citiesapps_com.md) / stadt-melk.at
- [Mettersdorf am Saßbach](/doc/source/citiesapps_com.md) / mettersdorf.com
- [Miesenbach](/doc/source/citiesapps_com.md) / miesenbach.at
- [Millstatt](/doc/ics/muellapp_com.md) / muellapp.com
- [Mischendorf](/doc/source/citiesapps_com.md) / mischendorf.at
- [Mistelbach](/doc/source/citiesapps_com.md) / mistelbach.at
- [Mitterdorf an der Raab](/doc/source/citiesapps_com.md) / mitterdorf-raab.at
- [Moosburg](/doc/ics/muellapp_com.md) / muellapp.com
- [Mureck](/doc/source/citiesapps_com.md) / mureck.gv.at
- [Mönchhof](/doc/source/citiesapps_com.md) / moenchhof.at
- [Mörbisch am See](/doc/source/citiesapps_com.md) / moerbisch.gv.at
- [Mörtschach](/doc/ics/muellapp_com.md) / muellapp.com
- [Mühldorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Müll App](/doc/ics/muellapp_com.md) / muellapp.com
- [Münster](/doc/ics/muellapp_com.md) / muellapp.com
- [Neudau](/doc/source/citiesapps_com.md) / neudau.gv.at
- [Neudorf bei Parndorf](/doc/source/citiesapps_com.md) / neudorfbeiparndorf.at
- [Neudörfl](/doc/source/citiesapps_com.md) / neudoerfl.gv.at
- [Neufeld an der Leitha](/doc/source/citiesapps_com.md) / neufeld-leitha.at
- [Neumarkt am Wallersee](/doc/ics/muellapp_com.md) / muellapp.com
- [Neusiedl am See](/doc/source/citiesapps_com.md) / neusiedlamsee.at
- [Neustift bei Güssing](/doc/source/citiesapps_com.md) / xn--neustift-bei-gssing-jbc.at
- [Nickelsdorf](/doc/source/citiesapps_com.md) / nickelsdorf.gv.at
- [Niederneukirchen](/doc/source/citiesapps_com.md) / niederneukirchen.ooe.gv.at
- [Ober-Grafendorf](/doc/source/citiesapps_com.md) / gemeinde.ober-grafendorf.gv.at
- [Oberdrauburg](/doc/ics/muellapp_com.md) / muellapp.com
- [Oberndorf in Tirol](/doc/ics/muellapp_com.md) / muellapp.com
- [Oberpullendorf](/doc/source/citiesapps_com.md) / oberpullendorf.gv.at
- [Oberschützen](/doc/source/citiesapps_com.md) / oberschuetzen.at
- [Obertrum am See](/doc/ics/muellapp_com.md) / muellapp.com
- [Oberwart](/doc/source/citiesapps_com.md) / oberwart.gv.at
- [Oslip](/doc/source/citiesapps_com.md) / oslip.at
- [Ottendorf an der Rittschein](/doc/source/citiesapps_com.md) / ottendorf-rittschein.steiermark.at
- [Ottobrunn](/doc/ics/muellapp_com.md) / muellapp.com
- [Paldau](/doc/source/citiesapps_com.md) / paldau.gv.at
- [Pama](/doc/source/citiesapps_com.md) / gemeinde-pama.at
- [Pamhagen](/doc/source/citiesapps_com.md) / gemeinde-pamhagen.at
- [Parndorf](/doc/source/citiesapps_com.md) / gemeinde-parndorf.at
- [Paternion](/doc/ics/muellapp_com.md) / muellapp.com
- [Payerbach](/doc/source/citiesapps_com.md) / payerbach.at
- [Peggau](/doc/source/citiesapps_com.md) / peggau.at
- [Pernegg an der Mur](/doc/source/citiesapps_com.md) / pernegg.at
- [Pernegg im Waldviertel](/doc/source/citiesapps_com.md) / pernegg.info
- [Perschling](/doc/source/citiesapps_com.md) / perschling.at
- [Pfarrwerfen](/doc/source/citiesapps_com.md) / gemeinde.pfarrwerfen.at
- [Pilgersdorf](/doc/source/citiesapps_com.md) / pilgersdorf.at
- [Pinggau](/doc/source/citiesapps_com.md) / pinggau.gv.at
- [Pinkafeld](/doc/source/citiesapps_com.md) / pinkafeld.gv.at
- [Pischelsdorf am Kulm](/doc/source/citiesapps_com.md) / pischelsdorf.com
- [Podersdorf am See](/doc/source/citiesapps_com.md) / gemeindepodersdorfamsee.at
- [Poggersdorf](/doc/source/citiesapps_com.md) / gemeinde-poggersdorf.at
- [Poggersdorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Pottenstein](/doc/source/citiesapps_com.md) / pottenstein.at
- [Potzneusiedl](/doc/source/citiesapps_com.md) / potzneusiedl.at
- [Poysdorf](/doc/source/citiesapps_com.md) / poysdorf.at
- [Pregarten](/doc/source/citiesapps_com.md) / pregarten.at
- [Premstätten](/doc/source/citiesapps_com.md) / premstaetten.gv.at
- [Pöchlarn](/doc/source/citiesapps_com.md) / poechlarn.at
- [Pörtschach am Wörther See](/doc/ics/muellapp_com.md) / muellapp.com
- [Raach am Hochgebirge](/doc/source/citiesapps_com.md) / raach.at
- [Raasdorf](/doc/source/citiesapps_com.md) / raasdorf.gv.at
- [Radenthein](/doc/ics/muellapp_com.md) / muellapp.com
- [Radfeld](/doc/ics/muellapp_com.md) / muellapp.com
- [Radmer](/doc/source/citiesapps_com.md) / radmer.at
- [Ragnitz](/doc/source/citiesapps_com.md) / ragnitz.gv.at
- [Raiding](/doc/source/citiesapps_com.md) / raiding-online.at
- [Ramsau im Zillertal](/doc/ics/muellapp_com.md) / muellapp.com
- [Rangersdorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Rechnitz](/doc/source/citiesapps_com.md) / rechnitz.at/de
- [Reichenau](/doc/source/citiesapps_com.md) / reichenau.gv.at
- [Reichenau an der Rax](/doc/source/citiesapps_com.md) / reichenau.at
- [Reichenfels](/doc/ics/muellapp_com.md) / muellapp.com
- [Reith im Alpbachtal](/doc/ics/muellapp_com.md) / muellapp.com
- [Reißeck](/doc/ics/muellapp_com.md) / muellapp.com
- [Rennweg am Katschberg](/doc/ics/muellapp_com.md) / muellapp.com
- [Rohr bei Hartberg](/doc/source/citiesapps_com.md) / rohr-bei-hartberg.at
- [Rohr im Burgenland](/doc/source/citiesapps_com.md) / rohr-bgld.at
- [Rottenbach](/doc/source/citiesapps_com.md) / rottenbach.gv.at
- [Rudersdorf](/doc/source/citiesapps_com.md) / rudersdorf.at
- [Rust](/doc/source/citiesapps_com.md) / freistadt-rust.at
- [Saalfelden am Steinernen Meer](/doc/source/citiesapps_com.md) / stadtmarketing-saalfelden.at/de
- [Sachsenburg](/doc/ics/muellapp_com.md) / muellapp.com
- [Sankt Georgen an der Stiefing](/doc/source/citiesapps_com.md) / st-georgen-stiefing.gv.at
- [Sankt Gilgen](/doc/source/citiesapps_com.md) / gemgilgen.at
- [Sankt Oswald bei Plankenwarth](/doc/source/citiesapps_com.md) / sanktoswald.net
- [Schiefling am Wörthersee](/doc/ics/muellapp_com.md) / muellapp.com
- [Schleedorf](/doc/ics/muellapp_com.md) / muellapp.com
- [Schlins](/doc/source/citiesapps_com.md) / schlins.at
- [Schrattenberg](/doc/source/citiesapps_com.md) / schrattenberg.gv.at
- [Schwadorf](/doc/source/citiesapps_com.md) / schwadorf.gv.at
- [Schwarzenbach an der Pielach](/doc/source/citiesapps_com.md) / schwarzenbach-pielach.at
- [Schwaz](/doc/ics/muellapp_com.md) / muellapp.com
- [Schwoich](/doc/ics/muellapp_com.md) / muellapp.com
- [Schäffern](/doc/source/citiesapps_com.md) / schaeffern.gv.at
- [Schützen am Gebirge](/doc/source/citiesapps_com.md) / schuetzen-am-gebirge.at
- [Seeboden](/doc/ics/muellapp_com.md) / muellapp.com
- [Seeham](/doc/ics/muellapp_com.md) / muellapp.com
- [Seekirchen am Wallersee](/doc/ics/muellapp_com.md) / muellapp.com
- [Seiersberg-Pirka](/doc/source/citiesapps_com.md) / gemeindekurier.at
- [Siegendorf](/doc/source/citiesapps_com.md) / siegendorf.gv.at
- [Sigleß](/doc/source/citiesapps_com.md) / sigless.at
- [Sigmundsherberg](/doc/source/citiesapps_com.md) / sigmundsherberg.gv.at
- [Sinabelkirchen](/doc/source/citiesapps_com.md) / sinabelkirchen.eu
- [Spittal an der Drau](/doc/ics/muellapp_com.md) / muellapp.com
- [St. Andrä](/doc/ics/muellapp_com.md) / muellapp.com
- [St. Andrä](/doc/source/citiesapps_com.md) / st-andrae.gv.at
- [St. Andrä am Zicksee](/doc/source/citiesapps_com.md) / gemeinde-standrae.at
- [St. Anna am Aigen](/doc/source/citiesapps_com.md) / st-anna-aigen.gv.at
- [St. Egyden am Steinfeld](/doc/source/citiesapps_com.md) / st-egyden.at
- [St. Florian bei Linz](/doc/source/citiesapps_com.md) / st-florian.at
- [St. Georgen an der Leys](/doc/source/citiesapps_com.md) / stgeorgenleys.at
- [St. Jakob im Rosental](/doc/ics/muellapp_com.md) / muellapp.com
- [St. Jakob im Rosental](/doc/source/citiesapps_com.md) / st-jakob-rosental.gv.at
- [St. Johann in der Haide](/doc/source/citiesapps_com.md) / st-johann-haide.gv.at
- [St. Johann in Tirol](/doc/ics/muellapp_com.md) / muellapp.com
- [St. Konrad](/doc/source/citiesapps_com.md) / st-konrad.at
- [St. Lorenzen am Wechsel](/doc/source/citiesapps_com.md) / st-lorenzen-wechsel.at
- [St. Margareten im Rosental](/doc/ics/muellapp_com.md) / muellapp.com
- [St. Margarethen an der Raab](/doc/source/citiesapps_com.md) / st-margarethen-raab.at
- [St. Margarethen im Burgenland](/doc/source/citiesapps_com.md) / st-margarethen.at
- [St. Martin im Innkreis](/doc/source/citiesapps_com.md) / st-martin-innkreis.ooe.gv.at
- [St. Peter - Freienstein](/doc/source/citiesapps_com.md) / st-peter-freienstein.gv.at
- [St. Peter am Ottersbach](/doc/source/citiesapps_com.md) / st-peter-ottersbach.gv.at
- [St. Ruprecht an der Raab](/doc/source/citiesapps_com.md) / st.ruprecht.at
- [St. Symvaro](/doc/ics/muellapp_com.md) / muellapp.com
- [St. Veit in der Südsteiermark](/doc/source/citiesapps_com.md) / st-veit-suedsteiermark.gv.at
- [Stadt Salzburg](/doc/source/infeo_at.md) / stadt-salzburg.at
- [Stadtgemeinde Traiskirchen](/doc/ics/traiskirchen_gv_at.md) / traiskirchen.gv.at
- [Stadtservice Korneuburg](/doc/source/korneuburg_stadtservice_at.md) / korneuburg.gv.at
- [Stall](/doc/ics/muellapp_com.md) / muellapp.com
- [Statzendorf](/doc/source/citiesapps_com.md) / statzendorf.at
- [Stegersbach](/doc/source/citiesapps_com.md) / gemeinde.stegersbach.at
- [Steinbrunn](/doc/source/citiesapps_com.md) / steinbrunn.at
- [Steinfeld](/doc/ics/muellapp_com.md) / muellapp.com
- [Steuerberg](/doc/source/citiesapps_com.md) / steuerberg.at
- [Stinatz](/doc/source/citiesapps_com.md) / stinatz.gv.at
- [Stiwoll](/doc/source/citiesapps_com.md) / stiwoll.at
- [Stockenboi](/doc/ics/muellapp_com.md) / muellapp.com
- [Stockerau](/doc/source/citiesapps_com.md) / stockerau.at
- [Straden](/doc/source/citiesapps_com.md) / straden.gv.at
- [Strass im Zillertal](/doc/ics/muellapp_com.md) / muellapp.com
- [Straß in Steiermark](/doc/source/citiesapps_com.md) / strass-steiermark.gv.at
- [Straßwalchen](/doc/ics/muellapp_com.md) / muellapp.com
- [Stubenberg](/doc/source/citiesapps_com.md) / stubenberg.gv.at
- [Stössing](/doc/source/citiesapps_com.md) / stoessing.gv.at
- [Söchau](/doc/source/citiesapps_com.md) / soechau.steiermark.at
- [Söll](/doc/ics/muellapp_com.md) / muellapp.com
- [Tadten](/doc/source/citiesapps_com.md) / tadten.at
- [Tattendorf](/doc/source/citiesapps_com.md) / tattendorf.at
- [Taufkirchen an der Trattnach](/doc/source/citiesapps_com.md) / taufkirchen.at/home
- [Techelsberg am Wörther See](/doc/ics/muellapp_com.md) / muellapp.com
- [Thal](/doc/source/citiesapps_com.md) / thal.gv.at
- [Tieschen](/doc/source/citiesapps_com.md) / tieschen.gv.at
- [Tobaj](/doc/source/citiesapps_com.md) / tobaj.gv.at
- [Trebesing](/doc/ics/muellapp_com.md) / muellapp.com
- [Treffen am Ossiacher See](/doc/ics/muellapp_com.md) / muellapp.com
- [Tulln an der Donau](/doc/source/citiesapps_com.md) / tulln.at
- [Umweltprofis](/doc/source/data_umweltprofis_at.md) / umweltprofis.at
- [Umweltv](/doc/ics/abfallv_zerowaste_io.md) / abfallv.zerowaste.io
- [Unterfrauenhaid](/doc/source/citiesapps_com.md) / unterfrauenhaid.at
- [Unterkohlstätten](/doc/source/citiesapps_com.md) / unterkohlstaetten.at
- [Unterlamm](/doc/source/citiesapps_com.md) / unterlamm.gv.at
- [Unterwart](/doc/source/citiesapps_com.md) / unterwart.at
- [Vasoldsberg](/doc/source/citiesapps_com.md) / vasoldsberg.gv.at
- [Velden am Wörther See](/doc/ics/muellapp_com.md) / muellapp.com
- [Villach](/doc/ics/muellapp_com.md) / muellapp.com
- [Villach](/doc/source/citiesapps_com.md) / villach.at
- [Vordernberg](/doc/source/citiesapps_com.md) / vordernberg.steiermark.at
- [Vorderstoder](/doc/source/citiesapps_com.md) / vorderstoder.ooe.gv.at
- [Völkermarkt](/doc/ics/muellapp_com.md) / muellapp.com
- [Völkermarkt](/doc/source/citiesapps_com.md) / voelkermarkt.gv.at
- [Walpersbach](/doc/source/citiesapps_com.md) / walpersbach.gv.at
- [Wartberg ob der Aist](/doc/source/citiesapps_com.md) / wartberg-aist.at
- [Wattens](/doc/ics/muellapp_com.md) / muellapp.com
- [Weiden am See](/doc/source/citiesapps_com.md) / weiden-see.at
- [Weitersfeld](/doc/source/citiesapps_com.md) / weitersfeld.gv.at
- [Weiz](/doc/source/citiesapps_com.md) / weiz.at
- [Weißenkirchen in der Wachau](/doc/source/citiesapps_com.md) / weissenkirchen-wachau.at
- [Weißensee](/doc/ics/muellapp_com.md) / muellapp.com
- [Weppersdorf](/doc/source/citiesapps_com.md) / weppersdorf.at
- [Werfenweng](/doc/source/citiesapps_com.md) / gemeinde-werfenweng.at
- [Wies](/doc/source/citiesapps_com.md) / wies.at
- [Wiesen](/doc/source/citiesapps_com.md) / wiesen.eu
- [Wiesfleck](/doc/source/citiesapps_com.md) / gemeinde-wiesfleck.at
- [Wiesmath](/doc/source/citiesapps_com.md) / wiesmath.at
- [Wimpassing an der Leitha](/doc/source/citiesapps_com.md) / wimpassing-leitha.at
- [Winden am See](/doc/source/citiesapps_com.md) / winden.at
- [Winklarn](/doc/source/citiesapps_com.md) / winklarn.gv.at
- [Winklern](/doc/ics/muellapp_com.md) / muellapp.com
- [Wolfau](/doc/source/citiesapps_com.md) / gemeinde-wolfau.at
- [Wolfsberg](/doc/ics/muellapp_com.md) / muellapp.com
- [Wolfsberg](/doc/source/citiesapps_com.md) / wolfsberg.at
- [Wolkersdorf im Weinviertel](/doc/source/citiesapps_com.md) / wolkersdorf.at
- [WSZ Moosburg](/doc/source/wsz_moosburg_at.md) / wsz-moosburg.at
- [Wulkaprodersdorf](/doc/source/citiesapps_com.md) / wulkaprodersdorf.at
- [Wörterberg](/doc/source/citiesapps_com.md) / woerterberg.at
- [Zagersdorf](/doc/source/citiesapps_com.md) / zagersdorf.at
- [Zelking-Matzleinsdorf](/doc/source/citiesapps_com.md) / zelking-matzleinsdorf.gv.at
- [Zell](/doc/ics/muellapp_com.md) / muellapp.com
- [Zell am Ziller](/doc/ics/muellapp_com.md) / muellapp.com
- [Zellberg](/doc/ics/muellapp_com.md) / muellapp.com
- [Zillingtal](/doc/source/citiesapps_com.md) / zillingtal.eu
- [Zurndorf](/doc/source/citiesapps_com.md) / zurndorf.at
- [Zwischenwasser](/doc/source/citiesapps_com.md) / zwischenwasser.at
- [Übelbach](/doc/source/citiesapps_com.md) / uebelbach.gv.at
</details>

<details>
<summary>Belgium</summary>

- [Hygea](/doc/source/hygea_be.md) / hygea.be
- [Limburg.net](/doc/ics/limburg_net.md) / limburg.net
- [Recycle!](/doc/source/recycleapp_be.md) / recycleapp.be
</details>

<details>
<summary>Canada</summary>

- [Aurora (ON)](/doc/source/recyclecoach_com.md) / aurora.ca
- [Calgary (AB)](/doc/source/calgary_ca.md) / calgary.ca
- [Calgary, AB](/doc/ics/recollect.md) / calgary.ca
- [City of Edmonton, AB](/doc/ics/recollect.md) / edmonton.ca
- [City of Greater Sudbury, ON](/doc/ics/recollect.md) / greatersudbury.ca
- [City of Nanaimo](/doc/ics/recollect.md) / nanaimo.ca
- [City of Peterborough, ON](/doc/ics/recollect.md) / peterborough.ca
- [City of Vancouver](/doc/ics/recollect.md) / vancouver.ca
- [County of Simcoe, ON](/doc/ics/recollect.md) / simcoe.ca
- [CURBit St. John's](/doc/ics/recollect.md) / curbitstjohns.ca
- [Halifax, NS](/doc/ics/recollect.md) / halifax.ca
- [Kawartha Lakes (ON)](/doc/source/recyclecoach_com.md) / kawarthalakes.ca
- [London (ON)](/doc/source/recyclecoach_com.md) / london.ca
- [Montreal (QC)](/doc/source/montreal_ca.md) / montreal.ca/info-collectes
- [Niagara Region](/doc/ics/recollect.md) / niagararegion.ca
- [Orillia, Ontario](/doc/source/orillia_ca.md) / orillia.ca
- [Ottawa, Canada](/doc/ics/recollect.md) / ottawa.ca
- [Peel Region, ON](/doc/ics/recollect.md) / peelregion.ca
- [Region of Waterloo](/doc/ics/recollect.md) / regionofwaterloo.ca
- [Richmond Hill (ON)](/doc/source/recyclecoach_com.md) / richmondhill.ca
- [RM of Morris, MB](/doc/ics/recollect.md) / mwmenviro.ca
- [Strathcona County, ON](/doc/ics/recollect.md) / strathcona.ca
- [Toronto (ON)](/doc/source/toronto_ca.md) / toronto.ca
- [Vaughan (ON)](/doc/source/recyclecoach_com.md) / vaughan.ca
- [Waste Wise APPS](/doc/ics/recollect.md) / edmonton.ca
- [Winnipeg (MB)](/doc/source/myutility_winnipeg_ca.md) / myutility.winnipeg.ca
</details>

<details>
<summary>Czech Republic</summary>

- [Praha](/doc/source/api_golemio_cz.md) / api.golemio.cz/docs/openapi
- [Rudna u Prahy](/doc/source/mestorudna_cz.md) / rudnamesto.cz
</details>

<details>
<summary>Denmark</summary>

- [Affaldonline](/doc/source/affaldonline_dk.md) / affaldonline.dk
- [Assens Forsyning](/doc/source/affaldonline_dk.md) / assensforsyning.dk
- [Fanø Kommune](/doc/source/affaldonline_dk.md) / fanoe.dk
- [Favrskov Forsyning](/doc/source/affaldonline_dk.md) / favrskovforsyning.dk
- [Fredericia Kommune Affald & Genbrug](/doc/source/affaldonline_dk.md) / affaldgenbrug-fredericia.dk
- [Kredsløb](/doc/ics/kredslob_dk.md) / kredslob.dk
- [Langeland Forsyning](/doc/source/affaldonline_dk.md) / langeland-forsyning.dk
- [Middelfart Kommune](/doc/source/affaldonline_dk.md) / middelfart.dk
- [Nyborg Forsyning & Service A/S](/doc/source/affaldonline_dk.md) / nfs.as
- [Odense Renovation](/doc/source/odenserenovation_dk.md) / odenserenovation.dk
- [Rebild Kommune](/doc/source/affaldonline_dk.md) / rebild.dk
- [Reno Djurs](/doc/source/renodjurs_dk.md) / renodjurs.dk
- [Renosyd](/doc/source/renosyd_dk.md) / renosyd.dk
- [RenoWeb](/doc/source/renoweb_dk.md) / renoweb.dk
- [Silkeborg Forsyning](/doc/source/affaldonline_dk.md) / silkeborgforsyning.dk
- [Sorø Kommune](/doc/source/affaldonline_dk.md) / soroe.dk
- [Vejle Kommune](/doc/source/affaldonline_dk.md) / vejle.dk
- [Vestforbrænding](/doc/source/vestfor_dk.md) / selvbetjening.vestfor.dk
- [Ærø Kommune](/doc/source/affaldonline_dk.md) / aeroekommune.dk
</details>

<details>
<summary>Finland</summary>

- [Kiertokapula Finland](/doc/source/kiertokapula_fi.md) / kiertokapula.fi
</details>

<details>
<summary>France</summary>

- [Mairie de Mamirolle](/doc/source/mamirolle_info.md) / mamirolle.info
- [Sivom Rive Droite - Bassens](/doc/source/sivom_rivedroite_fr.md) / sivom-rivedroite.fr
</details>

<details>
<summary>Germany</summary>

- [Aballwirtschaft Ludwigslust-Parchim AöR](/doc/ics/alp_lup_de.md) / alp-lup.de
- [Abfall App](/doc/ics/abfall_app_net.md) / abfall-app.net
- [Abfall IO ICS Version](/doc/ics/abfall_io_ics.md) / abfallplus.de
- [Abfall Stuttgart](/doc/source/stuttgart_de.md) / service.stuttgart.de
- [Abfall-Wirtschafts-Verband Nordschwaben](/doc/source/awido_de.md) / awv-nordschwaben.de
- [Abfall.IO / AbfallPlus](/doc/source/abfall_io.md) / abfallplus.de
- [Abfallbehandlungsgesellschaft Havelland mbH (abh)](/doc/source/abfall_havelland_de.md) / abfall-havelland.de
- [Abfallbewirtschaftung Ostalbkreis](/doc/source/abfall_io.md) / goa-online.de
- [Abfallentsorgung Kreis Kassel](/doc/ics/abfall_kreis_kassel_de.md) / abfall-kreis-kassel.de
- [Abfallkalender Hattingen](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderHattingen
- [Abfallkalender Herne](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderHerne
- [Abfallkalender Kassel](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderKassel
- [Abfallkalender Luebeck](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderLuebeck
- [Abfallkalender Mannheim](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderMannheim
- [Abfallkalender Offenbach](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderOffenbach
- [Abfallkalender Offenbach am Main (deprecated)](/doc/source/offenbach_de.md) / offenbach.de
- [Abfallkalender Würzburg](/doc/source/wuerzburg_de.md) / wuerzburg.de
- [AbfallNavi (RegioIT.de)](/doc/source/abfallnavi_de.md) / regioit.de
- [Abfalltermine Forchheim](/doc/source/abfalltermine_forchheim_de.md) / abfalltermine-forchheim.de
- [Abfallwirtschaft Alb-Donau-Kreis](/doc/source/buergerportal_de.md) / aw-adk.de
- [Abfallwirtschaft Altkreis Göttingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: lkgoettingen
- [Abfallwirtschaft Altkreis Osterode am Harz](/doc/source/app_abfallplus_de.md) / Abfall+ App: lkgoettingen
- [Abfallwirtschaft Dithmarschen (AWD)](/doc/ics/awd_online_de.md) / awd-online.de
- [Abfallwirtschaft Enzkreis](/doc/ics/entsorgung_regional_de.md) / entsorgung-regional.de
- [Abfallwirtschaft Freiburg](/doc/ics/abfallwirtschaft_freiburg_de.md) / abfall-eglz.de
- [Abfallwirtschaft Germersheim](/doc/source/abfallwirtschaft_germersheim_de.md) / abfallwirtschaft-germersheim.de
- [Abfallwirtschaft Isar-Inn](/doc/source/awido_de.md) / awv-isar-inn.de
- [Abfallwirtschaft Kreis Plön](/doc/ics/kreis_ploen_de.md) / kreis-ploen.de
- [Abfallwirtschaft Lahn-Dill-Kreises](/doc/source/awido_de.md) / awld.de
- [Abfallwirtschaft Landkreis Böblingen](/doc/ics/abfall_io_ics.md) / awb-bb.de
- [Abfallwirtschaft Landkreis Freudenstadt](/doc/source/abfall_io.md) / awb-fds.de
- [Abfallwirtschaft Landkreis Göppingen](/doc/ics/abfall_io_ics.md) / awb-gp.de
- [Abfallwirtschaft Landkreis Harburg](/doc/source/aw_harburg_de.md) / landkreis-harburg.de
- [Abfallwirtschaft Landkreis Haßberge](/doc/ics/awhas_de.md) / awhas.de
- [Abfallwirtschaft Landkreis Kitzingen](/doc/source/abfall_io.md) / abfallwelt.de
- [Abfallwirtschaft Landkreis Landsberg am Lech](/doc/source/abfall_io.md) / abfallberatung-landsberg.de
- [Abfallwirtschaft Landkreis Wolfenbüttel](/doc/source/alw_wf_de.md) / alw-wf.de
- [Abfallwirtschaft Neckar-Odenwald-Kreis](/doc/source/awn_de.md) / awn-online.de
- [Abfallwirtschaft Nürnberger Land](/doc/source/nuernberger_land_de.md) / nuernberger-land.de
- [Abfallwirtschaft Ortenaukreis](/doc/source/abfall_io.md) / abfallwirtschaft-ortenaukreis.de
- [Abfallwirtschaft Pforzheim](/doc/source/abfallwirtschaft_pforzheim_de.md) / abfallwirtschaft-pforzheim.de
- [Abfallwirtschaft Potsdam-Mittelmark (APM)](/doc/ics/apm_de.md) / apm-niemegk.de
- [Abfallwirtschaft Rems-Murr](/doc/source/awido_de.md) / abfallwirtschaft-rems-murr.de
- [Abfallwirtschaft Rendsburg](/doc/source/awr_de.md) / awr.de
- [Abfallwirtschaft Rheingau-Taunus-Kreis](/doc/source/c_trace_de.md) / eaw-rheingau-taunus.de
- [Abfallwirtschaft Sonneberg](/doc/ics/abfallwirtschaft_sonneberg_de.md) / abfallwirtschaft-sonneberg.de
- [Abfallwirtschaft Stadt Fürth](/doc/source/abfallwirtschaft_fuerth_eu.md) / abfallwirtschaft.fuerth.eu
- [Abfallwirtschaft Stadt Nürnberg](/doc/source/abfallnavi_de.md) / nuernberg.de
- [Abfallwirtschaft Stadt Schweinfurt](/doc/source/schweinfurt_de.md) / schweinfurt.de
- [Abfallwirtschaft Südholstein](/doc/source/awsh_de.md) / awsh.de
- [Abfallwirtschaft Werra-Meißner-Kreis](/doc/source/zva_wmk_de.md) / zva-wmk.de
- [Abfallwirtschafts-Zweckverband des Landkreises Hersfeld-Rotenburg](/doc/source/awido_de.md) / azv-hef-rof.de
- [Abfallwirtschaftsbetrieb Bergisch Gladbach](/doc/source/abfallnavi_de.md) / bergischgladbach.de
- [Abfallwirtschaftsbetrieb des Landkreises Pfaffenhofen a.d.Ilm (AWP)](/doc/ics/awp_landkreis_pfaffenhofen.md) / awp-paf.de
- [Abfallwirtschaftsbetrieb Emsland](/doc/source/awb_emsland_de.md) / awb-emsland.de
- [Abfallwirtschaftsbetrieb Esslingen](/doc/source/awb_es_de.md) / awb-es.de
- [Abfallwirtschaftsbetrieb Ilm-Kreis](/doc/ics/ilm_kreis_de.md) / ilm-kreis.de
- [Abfallwirtschaftsbetrieb Kiel (ABK)](/doc/source/abki_de.md) / abki.de
- [Abfallwirtschaftsbetrieb Landkreis Ahrweiler](/doc/source/meinawb_de.md) / meinawb.de
- [Abfallwirtschaftsbetrieb Landkreis Altenkirchen](/doc/source/awido_de.md) / awb-ak.de
- [Abfallwirtschaftsbetrieb Landkreis Augsburg](/doc/source/c_trace_de.md) / awb-landkreis-augsburg.de
- [Abfallwirtschaftsbetrieb Landkreis Aurich](/doc/source/c_trace_de.md) / mkw-grossefehn.de
- [Abfallwirtschaftsbetrieb Landkreis Karlsruhe](/doc/ics/awb_landkreis_karlsruhe_de.md) / awb-landkreis-karlsruhe.de
- [Abfallwirtschaftsbetrieb LK Mainz-Bingen](/doc/source/awb_mainz_bingen_de.md) / awb-mainz-bingen.de
- [Abfallwirtschaftsbetrieb Unstrut-Hainich-Kreis](/doc/ics/abfallwirtschaft_uhk_de.md) / abfallwirtschaft-uhk.de
- [Abfallwirtschaftsbetriebe Münster](/doc/source/muellmax_de.md) / stadt-muenster.de
- [Abfallwirtschaftsgesellschaft Landkreis Schaumburg](/doc/ics/aws_shg_de.md) / aws-shg.de
- [Abfallwirtschaftsverband Kreis Groß-Gerau](/doc/source/c_trace_de.md) / awv-gg.de
- [Abfallwirtschaftsverbandes Lippe](/doc/source/abfall_lippe_de.md) / abfall-lippe.de
- [Abfallwirtschaftszweckverband Wartburgkreis (AZV)](/doc/source/hausmuell_info.md) / azv-wak-ea.de
- [Abfallzweckverband Rhein-Mosel-Eifel (Landkreis Mayen-Koblenz)](/doc/source/abfall_io.md) / azv-rme.de
- [Abfuhrtermine.info](/doc/ics/abfuhrtermine_info.md) / abfuhrtermine.info
- [AHE Ennepe-Ruhr-Kreis](/doc/source/ahe_de.md) / ahe.de
- [AHK Heidekreis](/doc/source/ahk_heidekreis_de.md) / ahk-heidekreis.de
- [ALBA Berlin](/doc/source/abfall_io.md) / berlin.alba.info
- [ALBA Braunschweig](/doc/ics/alba_bs_de.md) / alba-bs.de
- [ALF Lahn-Fulda](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallhr
- [Allendorf](/doc/source/lobbe_app.md) / lobbe.app
- [Altena](/doc/source/lobbe_app.md) / lobbe.app
- [Altenbeken](/doc/source/lobbe_app.md) / lobbe.app
- [Altmarkkreis Salzwedel](/doc/ics/abfall_app_net.md) / altmarkkreis-salzwedel.de
- [Altötting (LK)](/doc/source/jumomind_de.md) / lra-aoe.de
- [Alzey-Worms](/doc/ics/kreis_alzey_worms_de.md) / kreis-alzey-worms.de/aktuelles/nichts-mehr-verpassen/abfalltermine
- [Apps by Abfall+](/doc/source/app_abfallplus_de.md) / abfallplus.de
- [Arnsberg](/doc/source/lobbe_app.md) / lobbe.app
- [ART Trier](/doc/ics/art_trier_de.md) / art-trier.de
- [ART Trier (Depreciated)](/doc/source/art_trier_de.md) / art-trier.de
- [Aschaffenburg (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [ASG Nordsachsen](/doc/source/abfall_io.md) / asg-nordsachsen.de
- [ASG Wesel](/doc/source/hausmuell_info.md) / asg-wesel.de
- [ASO Abfall-Service Osterholz](/doc/source/abfall_io.md) / aso-ohz.de
- [ASR Stadt Chemnitz](/doc/source/asr_chemnitz_de.md) / asr-chemnitz.de
- [ASTO (Abfall- Sammel- und Transportverband Oberberg)](/doc/ics/asto_de.md) / asto.de
- [ATHOS GmbH](/doc/source/app_abfallplus_de.md) / Abfall+ App: athosmobil
- [Attendorn](/doc/ics/abfuhrtermine_info.md) / attendorn.de
- [Augsburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: awa
- [Aurich (MKW)](/doc/source/jumomind_de.md) / mkw-grossefehn.de
- [AVL - Abfallverwertungsgesellschaft des Landkreises Ludwigsburg mbH](/doc/ics/avl_ludwigsburg_de.md) / avl-ludwigsburg.de
- [AWA Entsorgungs GmbH](/doc/source/abfallnavi_de.md) / awa-gmbh.de
- [AWB Abfallwirtschaft Vechta](/doc/source/abfallwirtschaft_vechta_de.md) / abfallwirtschaft-vechta.de
- [AWB Bad Kreuznach](/doc/source/awb_bad_kreuznach_de.md) / blupassionsystem.de/city/rest/garbageregion/filterRegion
- [AWB Köln](/doc/source/awbkoeln_de.md) / awbkoeln.de
- [AWB Landkreis Bad Dürkheim](/doc/source/awido_de.md) / awb.kreis-bad-duerkheim.de
- [AWB Landkreis Fürstenfeldbruck](/doc/source/awido_de.md) / awb-ffb.de
- [AWB Oldenburg](/doc/source/awb_oldenburg_de.md) / oldenburg.de
- [AWB Westerwaldkreis](/doc/source/abfall_io.md) / wab.rlp.de
- [AWG Bassum](/doc/ics/awg_bassum_de.md) / awg-bassum.de
- [AWG Donau-Wald](/doc/source/app_abfallplus_de.md) / Abfall+ App: zawdw
- [AWG Kreis Warendorf](/doc/source/abfallnavi_de.md) / awg-waf.de
- [AWIDO Online](/doc/source/awido_de.md) / awido-online.de
- [AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH](/doc/source/awigo_de.md) / awigo.de
- [AWISTA Düsseldorf](/doc/source/muellmax_de.md) / awista.de
- [AWISTA LOGISTIK Stadt Remscheid](/doc/source/monaloga_de.md) / monaloga.de
- [Awista Starnberg](/doc/ics/awista_starnberg_de.md) / awista-starnberg.de
- [AWL Neuss](/doc/source/awlneuss_de.md) / buergerportal.awl-neuss.de
- [AWM München](/doc/source/awm_muenchen_de.md) / awm-muenchen.de
- [AZV Stadt und Landkreis Hof](/doc/ics/azv_hof_de.md) / azv-hof.de
- [Bad Arolsen](/doc/source/lobbe_app.md) / lobbe.app
- [Bad Arolsen (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Bad Berleburg](/doc/source/lobbe_app.md) / lobbe.app
- [Bad Driburg](/doc/source/lobbe_app.md) / lobbe.app
- [Bad Homburg vdH](/doc/source/jumomind_de.md) / bad-homburg.de
- [Bad Kissingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappbk
- [Bad Wünnenberg](/doc/source/lobbe_app.md) / lobbe.app
- [Bad-König](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Balve](/doc/source/lobbe_app.md) / lobbe.app
- [Bamberg (Stadt und Landkreis)](/doc/ics/abfalltermine_bamberg_de.md) / abfalltermine-bamberg.de
- [Barnim](/doc/source/jumomind_de.md) / kreiswerke-barnim.de
- [Battenberg](/doc/source/lobbe_app.md) / lobbe.app
- [Bau & Service Oberursel](/doc/source/c_trace_de.md) / bso-oberursel.de
- [Bau- und Entsorgungsbetrieb Emden](/doc/ics/bee_emden_de.md) / bee-emden.de
- [Bergischer Abfallwirtschaftverbund](/doc/source/abfallnavi_de.md) / bavweb.de
- [Berlin](/doc/source/app_abfallplus_de.md) / Abfall+ App: app
- [Berlin Recycling](/doc/source/berlin_recycling_de.md) / berlin-recycling.de
- [Berliner Stadtreinigungsbetriebe](/doc/source/bsr_de.md) / bsr.de
- [Bestwig](/doc/source/lobbe_app.md) / lobbe.app
- [Beverungen (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Bielefeld](/doc/source/bielefeld_de.md) / bielefeld.de
- [Blaue Tonne - Schlaue Tonne](/doc/ics/blauetonne_schlauetonne_de.md) / blauetonne-schlauetonne.de
- [Bogenschütz Entsorgung](/doc/source/infeo_at.md) / bogenschuetz-entsorgung.de
- [Bonn](/doc/source/app_abfallplus_de.md) / Abfall+ App: bonnorange
- [Borchen](/doc/source/lobbe_app.md) / lobbe.app
- [Borgentreich](/doc/source/lobbe_app.md) / lobbe.app
- [Brakel](/doc/source/lobbe_app.md) / lobbe.app
- [Braunschweig](/doc/source/app_abfallplus_de.md) / Abfall+ App: app
- [Breckerfeld](/doc/source/lobbe_app.md) / lobbe.app
- [Bremer Stadtreinigung](/doc/source/c_trace_de.md) / die-bremer-stadtreinigung.de
- [Brensbach](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Breuberg](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Brilon](/doc/source/lobbe_app.md) / lobbe.app
- [Brombachtal](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Bromskirchen](/doc/source/lobbe_app.md) / lobbe.app
- [Burgenland (Landkreis)](/doc/source/app_abfallplus_de.md) / Abfall+ App: udb
- [Burgwald](/doc/source/lobbe_app.md) / lobbe.app
- [Büren](/doc/source/lobbe_app.md) / lobbe.app
- [Bürgerportal](/doc/source/buergerportal_de.md) / c-trace.de
- [Bürgerportal Bedburg](/doc/source/buergerportal_de.md) / bedburg.de
- [C-Trace](/doc/source/c_trace_de.md) / c-trace.de
- [Cederbaum Braunschweig](/doc/source/cederbaum_de.md) / cederbaum.de
- [Celle](/doc/source/jumomind_de.md) / zacelle.de
- [Cham Landkreis](/doc/ics/entsorgung_cham_de.md) / entsorgung-cham.de
- [Chemnitz (ASR)](/doc/source/hausmuell_info.md) / asr-chemnitz.de
- [Chiemgau Recycling - Landkreis Rosenheim](/doc/source/chiemgau_recycling_lk_rosenheim.md) / chiemgau-recycling.de
- [City of Karlsruhe](/doc/source/karlsruhe_de.md) / karlsruhe.de
- [CM City Media - Müllkalender](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Coburg Entsorgungs- und Baubetrieb CEB](/doc/source/ceb_coburg_de.md) / ceb-coburg.de
- [Darmstadt (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Darmstadt-Dieburg (ZAW)](/doc/source/jumomind_de.md) / zaw-online.de
- [Delbrück](/doc/source/lobbe_app.md) / lobbe.app
- [Diemelsee](/doc/source/lobbe_app.md) / lobbe.app
- [Diemelstadt](/doc/source/lobbe_app.md) / lobbe.app
- [Dillingen Saar](/doc/source/dillingen_saar_de.md) / dillingen-saar.de
- [Dinslaken](/doc/source/abfallnavi_de.md) / dinslaken.de
- [Drekopf](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallplaner
- [Drolshagen](/doc/ics/abfuhrtermine_info.md) / drolshagen.de
- [Duisburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwbd
- [EAD Darmstadt](/doc/source/ead_darmstadt_de.md) / ead.darmstadt.de
- [ebwo - Entsorgungs- und Baubetrieb Anstalt des öffentlichen Rechts der Stadt Worms](/doc/ics/worms_de.md) / worms.de/de/web/ebwo
- [Edertal](/doc/source/lobbe_app.md) / lobbe.app
- [EDG Entsorgung Dortmund](/doc/ics/edg_de.md) / edg.de
- [EGN Abfallkalender](/doc/source/egn_abfallkalender_de.md) / egn-abfallkalender.de
- [EGST Steinfurt](/doc/source/abfall_io.md) / egst.de
- [EGW Westmünsterland](/doc/source/abfallnavi_de.md) / egw.de
- [Eichsfeldwerke GmbH](/doc/source/hausmuell_info.md) / eichsfeldwerke.de
- [Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße](/doc/source/eigenbetrieb_abfallwirtschaft_de.md) / eigenbetrieb-abfallwirtschaft.de
- [Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl](/doc/source/hausmuell_info.md) / ebkds.de
- [EKM Mittelsachsen GmbH](/doc/ics/ekm_mittelsachsen_de.md) / ekm-mittelsachsen.de
- [Entsorgung Dortmund GmbH (EDG)](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallapp
- [Entsorgungs- und Wirtschaftsbetrieb Landau in der Pfalz](/doc/source/c_trace_de.md) / ew-landau.de
- [Entsorgungsbetrieb Märkisch-Oderland](/doc/ics/entsorgungsbetrieb_mol_de.md) / entsorgungsbetrieb-mol.de
- [Entsorgungsbetrieb Stadt Mainz](/doc/source/muellmax_de.md) / eb-mainz.de
- [Entsorgungsbetriebe Essen](/doc/source/abfall_io.md) / ebe-essen.de
- [Entsorgungsgesellschaft Görlitz-Löbau-Zittau](/doc/ics/abfall_eglz_de.md) / abfall-eglz.de
- [Entsorgungstermine Jena](/doc/ics/entsorgungstermine_jena_de.md) / entsorgungstermine.jena.de
- [Erbach](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Erfstadt (inoffical)](/doc/ics/abfallkalender_erftstadt_de.md) / abfallkalender-erftstadt.de
- [Esens (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [ESG Soest - Entsorgungswirtschaft Soest GmbH](/doc/ics/esg_soest_de.md) / esg-soest.de
- [Eslohe](/doc/source/lobbe_app.md) / lobbe.app
- [Essen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallebe
- [EVA Abfallentsorgung](/doc/ics/eva_abfallentsorgung_de.md) / eva-abfallentsorgung.de
- [EVS Entsorgungsverband Saar](/doc/source/muellmax_de.md) / evs.de
- [FES Frankfurter Entsorgungs- und Service GmbH](/doc/ics/fes_frankfurt_de.md) / fes-frankfurt.de
- [Finnentrop](/doc/ics/abfuhrtermine_info.md) / finnentrop.info
- [Flensburg (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Flörsheim Am Main](/doc/ics/floersheim_umweltkalender_de.md) / floersheim-umweltkalender.de
- [Frankenau](/doc/source/lobbe_app.md) / lobbe.app
- [Frankfurt (Oder)](/doc/source/app_abfallplus_de.md) / Abfall+ App: unterallgaeu
- [Frankfurt (Oder)](/doc/source/app_abfallplus_de.md) / Abfall+ App: willkommen
- [Freiburg im Breisgau](/doc/source/app_abfallplus_de.md) / Abfall+ App: asf
- [Fränkisch-Crumbach](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Gelber Sack Stuttgart](/doc/ics/gelbersack_stuttgart_de.md) / gelbersack-stuttgart.de
- [Gelsendienste Gelsenkirchen](/doc/ics/gelsendienste_de.md) / gelsendienste.de
- [Gemeinde Blankenheim](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Gemeinde Deggenhausertal](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Gemeinde Kalletal](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Gemeinde Roetgen](/doc/source/abfallnavi_de.md) / roetgen.de
- [Gemeinde Schutterwald](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Gemeinde Unterhaching](/doc/source/awido_de.md) / unterhaching.de
- [Gipsprojekt](/doc/ics/gipsprojekt_de.md) / gipsprojekt.de
- [Großkrotzenburg (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [GSAK APP / Krefeld](/doc/source/insert_it_de.md) / insert-it.de/BmsAbfallkalenderKrefeld
- [GWA - Kreis Unna mbH](/doc/source/abfallnavi_de.md) / gwa-online.de
- [Göttinger Entsorgungsbetriebe](/doc/source/abfall_io.md) / geb-goettingen.de
- [Gütersloh](/doc/source/abfallnavi_de.md) / guetersloh.de
- [Hagen](/doc/source/app_abfallplus_de.md) / Abfall+ App: hebhagen
- [Hainburg (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Hallenberg](/doc/source/lobbe_app.md) / lobbe.app
- [Hallesche Wasser und Stadtwirtschaft GmbH](/doc/ics/hws_halle_de.md) / hws-halle.de
- [Halver](/doc/source/abfallnavi_de.md) / halver.de
- [Halver](/doc/source/lobbe_app.md) / lobbe.app
- [Hattersheim am Main](/doc/source/jumomind_de.md) / hattersheim.de
- [Hatzfeld](/doc/source/lobbe_app.md) / lobbe.app
- [hausmüll.info](/doc/source/hausmuell_info.md) / hausmuell.info
- [Havelland](/doc/source/app_abfallplus_de.md) / Abfall+ App: app
- [Heidelberg](/doc/ics/gipsprojekt_de.md) / heidelberg.de
- [Heilbronn Entsorgungsbetriebe](/doc/source/heilbronn_de.md) / heilbronn.de
- [Heinz-Entsorgung (Landkreis Freising)](/doc/ics/heinz_entsorgung_de.md) / heinz-entsorgung.de
- [Hemer](/doc/source/lobbe_app.md) / lobbe.app
- [Herten (durth-roos.de)](/doc/ics/herten_de.md) / herten.de
- [Hohenlohekreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: hokwaste
- [Holtgast (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [HubertSchmid Recycling und Umweltschutz GmbH](/doc/source/api_hubert_schmid_de.md) / hschmid24.de/BlaueTonne
- [Höchst](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Höxter](/doc/source/jumomind_de.md) / abfallservice.kreis-hoexter.de
- [Ilm-Kreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappik
- [Ingolstadt](/doc/source/jumomind_de.md) / in-kb.de
- [Insert IT Apps](/doc/source/insert_it_de.md) / insert-infotech.de
- [Iserlohn](/doc/source/lobbe_app.md) / lobbe.app
- [Jumomind](/doc/source/jumomind_de.md) / jumomind.de
- [KAEV Niederlausitz](/doc/source/kaev_niederlausitz.md) / kaev.de
- [Kamp-Lintfort (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [KECL Kommunalentsorgung Chemnitzer Land](/doc/ics/kecl_de.md) / kecl.de
- [Kierspe](/doc/source/lobbe_app.md) / lobbe.app
- [Kirchdorf (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Kommunalservice Landkreis Börde AöR](/doc/source/ks_boerde_de.md) / ks-boerde.de
- [Korbach](/doc/source/lobbe_app.md) / lobbe.app
- [Kreis Ahrweiler](/doc/source/app_abfallplus_de.md) / Abfall+ App: meinawb
- [Kreis Augsburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallapp
- [Kreis Bad Kissingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallscout
- [Kreis Bautzen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfalllkbz
- [Kreis Bayreuth](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfalllkbt
- [Kreis Bergstraße](/doc/source/app_abfallplus_de.md) / Abfall+ App: zakb
- [Kreis Biberach](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallapp
- [Kreis Breisgau-Hochschwarzwald](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappbh
- [Kreis Calw](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallinfocw
- [Kreis Cloppenburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappclp
- [Kreis Coesfeld](/doc/source/abfallnavi_de.md) / wbc-coesfeld.de
- [Kreis Cuxhaven](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappcux
- [Kreis Diepholz](/doc/source/app_abfallplus_de.md) / Abfall+ App: awgbassum
- [Kreis Emmendingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: lkemmendingen
- [Kreis Emsland](/doc/source/app_abfallplus_de.md) / Abfall+ App: awbemsland
- [Kreis Freudenstadt](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappfds
- [Kreis Fürth](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappfuerth
- [Kreis Garmisch-Partenkirchen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappgap
- [Kreis Göppingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: awbgp
- [Kreis Heilbronn](/doc/source/app_abfallplus_de.md) / Abfall+ App: de
- [Kreis Heinsberg](/doc/source/abfallnavi_de.md) / kreis-heinsberg.de
- [Kreis Karlsruhe](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappka
- [Kreis Kitzingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwelt
- [Kreis Landsberg am Lech](/doc/source/app_abfallplus_de.md) / Abfall+ App: llabfallapp
- [Kreis Landshut](/doc/source/app_abfallplus_de.md) / Abfall+ App: landshutlk
- [Kreis Limburg-Weilburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: meinawblm
- [Kreis Ludwigsburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: avlserviceplus
- [Kreis Lörrach](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallapploe
- [Kreis Mayen-Koblenz](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappmyk
- [Kreis Miesbach](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappvivo
- [Kreis Miltenberg](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappmil
- [Kreis Märkisch-Oderland](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappmol
- [Kreis Neustadt/Aisch-Bad Windsheim](/doc/source/app_abfallplus_de.md) / Abfall+ App: neustadtaisch
- [Kreis Neuwied](/doc/source/app_abfallplus_de.md) / Abfall+ App: muellwecker_neuwied
- [Kreis Nienburg / Weser](/doc/source/app_abfallplus_de.md) / Abfall+ App: bawnapp
- [Kreis Nordfriesland](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappnf
- [Kreis Ostallgäu](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappoal
- [Kreis Osterholz](/doc/source/app_abfallplus_de.md) / Abfall+ App: asoapp
- [Kreis Pinneberg](/doc/source/abfallnavi_de.md) / kreis-pinneberg.de
- [Kreis Rastatt](/doc/source/app_abfallplus_de.md) / Abfall+ App: awbrastatt
- [Kreis Ravensburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallapprv
- [Kreis Reutlingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallkreisrt
- [Kreis Rotenburg (Wümme)](/doc/source/app_abfallplus_de.md) / Abfall+ App: awrplus
- [Kreis Schaumburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: aws
- [Kreis Sigmaringen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappsig
- [Kreis Starnberg](/doc/source/app_abfallplus_de.md) / Abfall+ App: awistasta
- [Kreis Steinburg](/doc/ics/steinburg_de.md) / steinburg.de
- [Kreis Steinfurt](/doc/source/app_abfallplus_de.md) / Abfall+ App: egst
- [Kreis Südwestpfalz](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfalllkswp
- [Kreis Traunstein](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappts
- [Kreis Uelzen](/doc/source/app_abfallplus_de.md) / Abfall+ App: lkruelzen
- [Kreis Vechta](/doc/source/app_abfallplus_de.md) / Abfall+ App: awvapp
- [Kreis Viersen](/doc/source/abfallnavi_de.md) / kreis-viersen.de
- [Kreis Vorpommern-Rügen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappvorue
- [Kreis Weißenburg-Gunzenhausen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappwug
- [Kreis Wesermarsch](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappgib
- [Kreis Würzburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: teamorange
- [Kreisstadt Dietzenbach](/doc/source/c_trace_de.md) / dietzenbach.de
- [Kreisstadt Friedberg](/doc/source/muellmax_de.md) / friedberg-hessen.de
- [Kreisstadt Groß-Gerau](/doc/ics/gross_gerau_de.md) / gross-gerau.de
- [Kreisstadt St. Wendel](/doc/source/c_trace_de.md) / sankt-wendel.de
- [Kreiswerke Schmalkalden-Meiningen GmbH](/doc/source/hausmuell_info.md) / kwsm.de
- [Kreiswirtschaftsbetriebe Goslar](/doc/source/kwb_goslar_de.md) / kwb-goslar.de
- [Kreuztal](/doc/ics/abfuhrtermine_info.md) / kreuztal.de
- [Kronberg im Taunus](/doc/source/abfallnavi_de.md) / kronberg.de
- [KV Cochem-Zell](/doc/source/buergerportal_de.md) / cochem-zell-online.de
- [KWU Entsorgung Landkreis Oder-Spree](/doc/source/kwu_de.md) / kwu-entsorgung.de
- [Landkreis Amberg-Sulzbach](/doc/ics/landkreis_as_de.md) / landkreis-as.de
- [Landkreis Anhalt-Bitterfeld](/doc/ics/abikw_de.md) / abikw.de
- [Landkreis Ansbach](/doc/source/awido_de.md) / landkreis-ansbach.de
- [Landkreis Aschaffenburg](/doc/source/awido_de.md) / landkreis-aschaffenburg.de
- [Landkreis Aschaffenburg (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Bayreuth](/doc/source/abfall_io.md) / landkreis-bayreuth.de
- [Landkreis Berchtesgadener Land](/doc/source/awido_de.md) / lra-bgl.de
- [Landkreis Biberach (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Böblingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappbb
- [Landkreis Böblingen](/doc/ics/abfall_app_net.md) / lrabb.de
- [Landkreis Börde AöR (KsB)](/doc/source/hausmuell_info.md) / ks-boerde.de
- [Landkreis Calw](/doc/source/abfall_io.md) / kreis-calw.de
- [Landkreis Coburg](/doc/source/awido_de.md) / landkreis-coburg.de
- [Landkreis Cuxhaven](/doc/source/abfall_io.md) / landkreis-cuxhaven.de
- [Landkreis Eichstätt (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Erding](/doc/source/awido_de.md) / landkreis-erding.de
- [Landkreis Erlangen-Höchstadt](/doc/source/erlangen_hoechstadt_de.md) / erlangen-hoechstadt.de
- [Landkreis Esslingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappes
- [Landkreis Friesland (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Fulda](/doc/source/awido_de.md) / landkreis-fulda.de
- [Landkreis Gießen](/doc/source/muellmax_de.md) / lkgi.de
- [Landkreis Gifhorn](/doc/source/abfallkalender_gifhorn_de.md) / abfallkalender-gifhorn.de
- [Landkreis Gotha](/doc/source/awido_de.md) / landkreis-gotha.de
- [Landkreis Grafschaft](/doc/source/jumomind_de.md) / awb.grafschaft-bentheim.de
- [Landkreis Görlitz](/doc/source/app_abfallplus_de.md) / Abfall+ App: lkgr
- [Landkreis Günzburg](/doc/source/awido_de.md) / kaw.landkreis-guenzburg.de
- [Landkreis Hameln-Pyrmont](/doc/ics/hameln_pyrmont_de.md) / hameln-pyrmont.de
- [Landkreis Harz](/doc/source/jumomind_de.md) / enwi-hz.de
- [Landkreis Heidenheim](/doc/ics/abfall_hdh_de.md) / abfall-hdh.de
- [Landkreis Heilbronn](/doc/source/abfall_io.md) / landkreis-heilbronn.de
- [Landkreis Kelheim](/doc/source/awido_de.md) / landkreis-kelheim.de
- [Landkreis Kronach](/doc/source/awido_de.md) / landkreis-kronach.de
- [Landkreis Kulmbach](/doc/source/awido_de.md) / landkreis-kulmbach.de
- [Landkreis Kusel](/doc/source/landkreis_kusel_de.md) / landkreis-kusel.de
- [Landkreis Leer (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Leipzig](/doc/source/app_abfallplus_de.md) / Abfall+ App: leipziglk
- [Landkreis Limburg-Weilburg](/doc/source/abfall_io.md) / awb-lm.de
- [Landkreis Lüchow-Dannenberg](/doc/ics/abfall_app_net.md) / luechow-dannenberg.de
- [Landkreis Main-Spessart](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallmsp
- [Landkreis Mettmann (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Mühldorf a. Inn](/doc/source/awido_de.md) / lra-mue.de
- [Landkreis Nordwestmecklenburg](/doc/source/geoport_nwm_de.md) / geoport-nwm.de
- [Landkreis Northeim (unofficial)](/doc/ics/nerdbridge_de.md) / abfall.nerdbridge.de
- [Landkreis Ostallgäu](/doc/source/abfall_io.md) / buerger-ostallgaeu.de
- [Landkreis Paderborn (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Peine](/doc/ics/ab_peine_de.md) / ab-peine.de
- [Landkreis Ravensburg](/doc/source/rv_de.md) / rv.de
- [Landkreis Reutlingen](/doc/source/abfall_io.md) / kreis-reutlingen.de
- [Landkreis Rhön Grabfeld](/doc/source/landkreis_rhoen_grabfeld.md) / abfallinfo-rhoen-grabfeld.de
- [Landkreis Rosenheim](/doc/source/awido_de.md) / abfall.landkreis-rosenheim.de
- [Landkreis Rostock](/doc/source/abfall_lro_de.md) / abfall-lro.de
- [Landkreis Rotenburg (Wümme)](/doc/source/abfall_io.md) / lk-awr.de
- [Landkreis Roth](/doc/source/awido_de.md) / landratsamt-roth.de
- [Landkreis Roth](/doc/source/c_trace_de.md) / landratsamt-roth.de
- [Landkreis Rottweil](/doc/source/abfall_io.md) / landkreis-rottweil.de
- [Landkreis Schweinfurt](/doc/source/awido_de.md) / landkreis-schweinfurt.de
- [Landkreis Schwäbisch Hall](/doc/source/lrasha_de.md) / lrasha.de
- [Landkreis Sigmaringen](/doc/source/abfall_io.md) / landkreis-sigmaringen.de
- [Landkreis soest](/doc/ics/abfall_app_net.md) / kreis-soest.de
- [Landkreis Stade](/doc/ics/landkreis_stade_de.md) / landkreis-stade.de
- [Landkreis Stendal](/doc/ics/abfall_app_net.md) / landkreis-stendal.de
- [Landkreis Südliche Weinstraße](/doc/source/awido_de.md) / suedliche-weinstrasse.de
- [Landkreis Tirschenreuth](/doc/source/awido_de.md) / kreis-tir.de
- [Landkreis Tübingen](/doc/source/awido_de.md) / abfall-kreis-tuebingen.de
- [Landkreis Vogtland](/doc/ics/vogtlandkreis_de.md) / vogtlandkreis.de
- [Landkreis Weißenburg-Gunzenhausen](/doc/source/abfall_io.md) / landkreis-wug.de
- [Landkreis Wittmund](/doc/source/landkreis_wittmund_de.md) / landkreis-wittmund.de
- [Landkreis Wittmund (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Wittmund (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Landkreis Wunsiedel im Fichtelgebirge](/doc/source/app_abfallplus_de.md) / Abfall+ App: kufiapp
- [Landkreisbetriebe Neuburg-Schrobenhausen](/doc/source/awido_de.md) / landkreisbetriebe.de
- [Landratsamt Aichach-Friedberg](/doc/source/awido_de.md) / lra-aic-fdb.de
- [Landratsamt Bodenseekreis](/doc/ics/bodenseekreis_de.md) / bodenseekreis.de
- [Landratsamt Dachau](/doc/source/awido_de.md) / landratsamt-dachau.de
- [Landratsamt Main-Tauber-Kreis](/doc/source/c_trace_de.md) / main-tauber-kreis.de
- [Landratsamt Miltenberg](/doc/ics/landkreis_miltenberg_de.md) / landkreis-miltenberg.de
- [Landratsamt Regensburg](/doc/source/awido_de.md) / landkreis-regensburg.de
- [Landratsamt Traunstein](/doc/source/abfall_io.md) / traunstein.com
- [Landratsamt Unterallgäu](/doc/source/abfall_io.md) / landratsamt-unterallgaeu.de
- [Landshut](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappla
- [Langen](/doc/source/jumomind_de.md) / kbl-langen.de
- [Lebacher Abfallzweckverband (LAZ)](/doc/ics/lebach_de.md) / lebach.de
- [Lennestadt](/doc/ics/abfuhrtermine_info.md) / lennestadt.de
- [Leverkusen](/doc/source/app_abfallplus_de.md) / Abfall+ App: avea
- [Lichtenau](/doc/source/lobbe_app.md) / lobbe.app
- [Lichtenfels](/doc/source/lobbe_app.md) / lobbe.app
- [LK Schwandorf](/doc/ics/entsorgung_sad_de.md) / entsorgung-sad.de
- [Lobbe App](/doc/source/lobbe_app.md) / lobbe.app
- [Ludwigshafen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfalllu
- [Ludwigshafen am Rhein](/doc/source/abfall_io.md) / ludwigshafen.de
- [Lübbecke (Jumomind)](/doc/source/jumomind_de.md) / luebbecke.de
- [Lübeck Entsorgungsbetriebe](/doc/ics/luebeck_de.md) / luebeck.de
- [Lützelbach](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [mags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR](/doc/source/mags_de.md) / mags.de
- [Main-Kinzig-Kreis](/doc/source/jumomind_de.md) / abfall-mkk.de
- [Main-Kinzig-Kreis (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Mannheim](/doc/source/app_abfallplus_de.md) / Abfall+ App: de
- [Marienmünster](/doc/source/lobbe_app.md) / lobbe.app
- [Marsberg](/doc/source/lobbe_app.md) / lobbe.app
- [Mechernich und Kommunen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallinfoapp
- [Medebach](/doc/source/lobbe_app.md) / lobbe.app
- [Mein-Abfallkalender.online](/doc/ics/mein_abfallkalender_online.md) / mein-abfallkalender.online
- [Meinerzhagen](/doc/source/lobbe_app.md) / lobbe.app
- [Menden](/doc/source/lobbe_app.md) / lobbe.app
- [Meschede](/doc/source/lobbe_app.md) / lobbe.app
- [Metzingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappmetz
- [Michelstadt](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Minden](/doc/source/jumomind_de.md) / minden.de
- [Mossautal](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [MZV Biedenkopf](/doc/source/buergerportal_de.md) / mzv-biedenkopf.de
- [Mühlheim am Main (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Müllabfuhr Deutschland](/doc/source/muellabfuhr_de.md) / portal.muellabfuhr-deutschland.de
- [MüllALARM / Schönmackers](/doc/source/abfall_io.md) / schoenmackers.de
- [Müllmax](/doc/source/muellmax_de.md) / muellmax.de
- [München Landkreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: lkmabfallplus
- [Nachrodt-Wiblingwerde](/doc/source/lobbe_app.md) / lobbe.app
- [Neckar-Odenwald-Kreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappno
- [Nenndorf (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Neu Ulm](/doc/ics/neu_ulm_de.md) / neu-ulm.de
- [Neumünster (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Neunkirchen Siegerland](/doc/source/abfall_neunkirchen_siegerland_de.md) / neunkirchen-siegerland.de
- [Neustadt a.d. Waldnaab](/doc/source/awido_de.md) / neustadt.de
- [Neustadt an der Weinstraße](/doc/source/jumomind_de.md) / neustadt.eu
- [Nordsachsen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwecker
- [Oberhavel](/doc/source/app_abfallplus_de.md) / Abfall+ App: app
- [Oberhavel AWU](/doc/ics/awu_oberhavel_de.md) / awu-oberhavel.de
- [Oberzent](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Oldenburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappol
- [Olpe](/doc/ics/abfuhrtermine_info.md) / olpe.de
- [Olsberg](/doc/source/lobbe_app.md) / lobbe.app
- [Ortenaukreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappog
- [Ostholstein](/doc/source/jumomind_de.md) / zvo.com
- [Ostprignitz-Ruppin](/doc/source/app_abfallplus_de.md) / Abfall+ App: app
- [Plettenberg](/doc/source/lobbe_app.md) / lobbe.app
- [Potsdam](/doc/source/potsdam_de.md) / potsdam.de
- [Prignitz](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwecker
- [Prignitz](/doc/source/app_abfallplus_de.md) / Abfall+ App: unterallgaeu
- [Prignitz](/doc/source/app_abfallplus_de.md) / Abfall+ App: willkommen
- [Pullach im Isartal](/doc/source/awido_de.md) / pullach.de
- [Recklinghausen](/doc/source/jumomind_de.md) / zbh-ksr.de
- [RegioEntsorgung AöR](/doc/source/app_abfallplus_de.md) / Abfall+ App: regioentsorgung
- [RegioEntsorgung Städteregion Aachen](/doc/source/regioentsorgung_de.md) / regioentsorgung.de
- [Reichelsheim](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [RESO](/doc/source/reso_gmbh_de.md) / reso-gmbh.de
- [Rhein-Hunsrück (Jumomind)](/doc/source/jumomind_de.md) / rh-entsorgung.de
- [Rhein-Hunsrück Entsorgung (RHE)](/doc/source/rh_entsorgung_de.md) / rh-entsorgung.de
- [Rhein-Neckar-Kreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallavr
- [Rhein-Neckar-Kreis](/doc/source/abfall_io.md) / rhein-neckar-kreis.de
- [Rhein-Pfalz-Kreis](/doc/ics/abfall_app_net.md) / rhein-pfalz-kreis.de
- [Rosbach Vor Der Höhe](/doc/source/jumomind_de.md) / rosbach-hessen.de
- [Rosenthal](/doc/source/lobbe_app.md) / lobbe.app
- [Rottweil](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwecker
- [Rottweil](/doc/source/app_abfallplus_de.md) / Abfall+ App: unterallgaeu
- [Rottweil](/doc/source/app_abfallplus_de.md) / Abfall+ App: willkommen
- [RSAG Rhein-Sieg-Kreis](/doc/source/muellmax_de.md) / rsag.de
- [Rüthen](/doc/source/lobbe_app.md) / lobbe.app
- [Salzgitter (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Salzlandkreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallslk
- [Schalksmühle](/doc/source/lobbe_app.md) / lobbe.app
- [Schleswig-Flensburg (ASF)](/doc/ics/asf_online_de.md) / asf-online.de
- [Schmallenberg](/doc/source/lobbe_app.md) / lobbe.app
- [Schmitten im Taunus (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Schwarze Elster](/doc/source/app_abfallplus_de.md) / Abfall+ App: aevapp
- [Schwarzwald-Baar-Kreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallsbk
- [Schöneck (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Schönmackers](/doc/source/app_abfallplus_de.md) / Abfall+ App: muellalarm
- [Sector 27 - Datteln, Marl, Oer-Erkenschwick](/doc/source/sector27_de.md) / muellkalender.sector27.de
- [Seligenstadt (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Siegen](/doc/ics/siegen_stadt_de.md) / siegen-stadt.de
- [Stadt Aachen](/doc/source/abfallnavi_de.md) / aachen.de
- [Stadt Arnsberg](/doc/source/c_trace_de.md) / arnsberg.de
- [Stadt Bayreuth](/doc/source/c_trace_de.md) / bayreuth.de
- [Stadt Cottbus](/doc/source/abfallnavi_de.md) / cottbus.de
- [Stadt Darmstadt](/doc/source/muellmax_de.md) / darmstadt.de
- [Stadt Detmold](/doc/ics/detmold_de.md) / detmold.de
- [Stadt Dorsten](/doc/source/abfallnavi_de.md) / ebd-dorsten.de
- [Stadt Emmendingen](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Stadt Frankenberg (Eder)](/doc/source/frankenberg_de.md) / frankenberg.de
- [Stadt Fulda](/doc/source/awido_de.md) / fulda.de
- [Stadt Haltern am See](/doc/source/muellmax_de.md) / haltern-am-see.de
- [Stadt Hamm](/doc/source/muellmax_de.md) / hamm.de
- [Stadt Hanau](/doc/source/muellmax_de.md) / hanau.de
- [Stadt Kaufbeuren](/doc/source/awido_de.md) / kaufbeuren.de
- [Stadt Koblenz](/doc/ics/koblenz_de.md) / koblenz.de
- [Stadt Landshut](/doc/source/abfall_io.md) / landshut.de
- [Stadt Mainhausen](/doc/ics/stadt_mainhausen_de.md) / mainhausen.de
- [Stadt Maintal](/doc/source/muellmax_de.md) / maintal.de
- [Stadt Memmingen](/doc/source/awido_de.md) / umwelt.memmingen.de
- [Stadt Messstetten](/doc/source/cmcitymedia_de.md) / cmcitymedia.de
- [Stadt Norderstedt](/doc/source/abfallnavi_de.md) / betriebsamt-norderstedt.de
- [Stadt Osnabrück](/doc/ics/osnabrueck_de.md) / osnabrueck.de
- [Stadt Overath](/doc/source/c_trace_de.md) / overath.de
- [Stadt Regensburg](/doc/source/awido_de.md) / regensburg.de
- [Stadt Solingen](/doc/source/abfallnavi_de.md) / solingen.de
- [Stadt Spenge](/doc/ics/spenge_de.md) / spenge.de
- [Stadt Unterschleißheim](/doc/source/awido_de.md) / unterschleissheim.de
- [Stadtbetrieb Frechen](/doc/ics/stadtbetrieb_frechen_de.md) / stadtbetrieb-frechen.de
- [Stadtbildpflege Kaiserslautern](/doc/source/muellmax_de.md) / stadtbildpflege-kl.de
- [Stadtentsorgung Rostock](/doc/ics/stadtentsorgung_rostock_de.md) / stadtentsorgung-rostock.de
- [Stadtreinigung Dresden](/doc/source/stadtreinigung_dresden_de.md) / dresden.de
- [Stadtreinigung Hamburg](/doc/source/stadtreinigung_hamburg.md) / stadtreinigung.hamburg
- [Stadtreinigung Leipzig](/doc/ics/stadtreinigung_leipzig_de.md) / stadtreinigung-leipzig.de
- [Stadtreinigung Leipzig](/doc/source/stadtreinigung_leipzig_de.md) / stadtreinigung-leipzig.de
- [StadtService Brühl](/doc/source/stadtservice_bruehl_de.md) / stadtservice-bruehl.de
- [Stadtwerke Erfurt, SWE](/doc/source/hausmuell_info.md) / stadtwerke-erfurt.de
- [Stadtwerke Hürth](/doc/ics/stadtwerke_huerth_de.md) / stadtwerke-huerth.de
- [Steinheim](/doc/source/lobbe_app.md) / lobbe.app
- [STL Lüdenscheid](/doc/source/abfallnavi_de.md) / stl-luedenscheid.de
- [Städteservice Raunheim Rüsselsheim](/doc/source/staedteservice_de.md) / staedteservice.de
- [Sundern](/doc/source/lobbe_app.md) / lobbe.app
- [SWK Herford](/doc/ics/swk_herford_de.md) / swk.herford.de
- [Südbrandenburgischer Abfallzweckverband](/doc/source/sbazv_de.md) / sbazv.de
- [TBR Remscheid](/doc/source/muellmax_de.md) / tbr-info.de
- [TBV Velbert](/doc/source/tbv_velbert_de.md) / tbv-velbert.de
- [Team Orange (Landkreis Würzburg)](/doc/source/abfall_io.md) / team-orange.info
- [Technischer Betriebsdienst Reutlingen](/doc/ics/tbr_reutlingen_de.md) / tbr-reutlingen.de
- [tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen](/doc/source/tonnenleerung_de.md) / tonnenleerung.de
- [Tuttlingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwecker
- [Tuttlingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: unterallgaeu
- [Tuttlingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: willkommen
- [Twistetal](/doc/source/lobbe_app.md) / lobbe.app
- [Tübingen](/doc/source/app_abfallplus_de.md) / Abfall+ App: app
- [Uckermark](/doc/source/jumomind_de.md) / udg-uckermark.de
- [ULM (EBU)](/doc/ics/ebu_ulm_de.md) / ebu-ulm.de
- [Ulm (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [USB Bochum](/doc/source/muellmax_de.md) / usb-bochum.de
- [Usingen (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [VIVO Landkreis Miesbach](/doc/source/abfall_io.md) / vivowarngau.de
- [Volkmarsen (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Vöhl](/doc/source/lobbe_app.md) / lobbe.app
- [Vöhringen (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Waldshut](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallwecker
- [Waldshut](/doc/source/app_abfallplus_de.md) / Abfall+ App: unterallgaeu
- [Waldshut](/doc/source/app_abfallplus_de.md) / Abfall+ App: willkommen
- [Warburg](/doc/source/lobbe_app.md) / lobbe.app
- [Warstein](/doc/source/lobbe_app.md) / lobbe.app
- [WBO Wirtschaftsbetriebe Oberhausen](/doc/source/abfallnavi_de.md) / wbo-online.de
- [Wegberg (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Wenden](/doc/ics/abfuhrtermine_info.md) / gemeinde-wenden.de
- [Werdohl](/doc/source/lobbe_app.md) / lobbe.app
- [Wermelskirchen (Service Down)](/doc/source/wermelskirchen_de.md) / wermelskirchen.de
- [Westerholt (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Westerwaldkreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: wabapp
- [WGV Recycling GmbH](/doc/source/awido_de.md) / wgv-quarzbichl.de
- [Wilhelmshaven (MyMuell App)](/doc/source/jumomind_de.md) / mymuell.de
- [Willebadessen](/doc/source/lobbe_app.md) / lobbe.app
- [Willingen](/doc/source/lobbe_app.md) / lobbe.app
- [Winterberg](/doc/source/lobbe_app.md) / lobbe.app
- [Wolfsburger Abfallwirtschaft und Straßenreinigung](/doc/source/was_wolfsburg_de.md) / was-wolfsburg.de
- [WZV Kreis Segeberg](/doc/source/c_trace_de.md) / wzv.de
- [Würzburg](/doc/source/app_abfallplus_de.md) / Abfall+ App: wuerzburg
- [ZAH Hildesheim](/doc/ics/zah_hildesheim_de.md) / zah-hildesheim.de
- [ZAK Kempten](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallappzak
- [ZAW Donau-Wald](/doc/source/awg_de.md) / awg.de
- [ZAW-SR](/doc/source/app_abfallplus_de.md) / Abfall+ App: zawsr
- [ZBG Gladbeck](/doc/ics/zb_gladbeck_de.md) / zb-gladbeck.de
- [ZEW Zweckverband Entsorgungsregion West](/doc/source/abfallnavi_de.md) / zew-entsorgung.de
- [ZfA Iserlohn](/doc/ics/zfa_iserlohn_de.md) / zfa-iserlohn.de
- [Zollernalbkreis](/doc/source/app_abfallplus_de.md) / Abfall+ App: abfallzak
- [Zollernalbkreis](/doc/ics/abfall_io_ics.md) / zollernalbkreis.de
- [Zweckverband Abfallwirtschaft Kreis Bergstraße](/doc/source/zakb_de.md) / zakb.de
- [Zweckverband Abfallwirtschaft Oberes Elbtal](/doc/ics/zaoe_de.md) / zaoe.de
- [Zweckverband Abfallwirtschaft Region Hannover](/doc/source/aha_region_de.md) / aha-region.de
- [Zweckverband Abfallwirtschaft Saale-Orla](/doc/source/awido_de.md) / zaso-online.de
- [Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis](/doc/source/zva_sek_de.md) / zva-sek.de
- [Zweckverband Abfallwirtschaft Südwestsachsen (ZAS)](/doc/ics/za_sws_de.md) / za-sws.de
- [Zweckverband München-Südost](/doc/source/awido_de.md) / zvmso.de
</details>

<details>
<summary>Hungary</summary>

- [FKF Budapest](/doc/source/fkf_bp_hu.md) / fkf.hu
- [FKF Budaörs](/doc/source/fkf_bo_hu.md) / fkf.hu
- [ÉTH (Érd, Diósd, Nagytarcsa, Sóskút, Tárnok)](/doc/source/eth_erd_hu.md) / eth-erd.hu
</details>

<details>
<summary>Italy</summary>

- [Agliana](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Alia Servizi Ambientali S.p.A.](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Bagno a Ripoli](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Barberino di Mugello](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Barberino Tavarnelle](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Borgo San Lorenzo](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Buggiano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Calenzano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Campi Bisenzio](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Cantagallo](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Capraia e Limite](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Carmignano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Castelfiorentino](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Cerreto Guidi](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Certaldo](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Chiesina Uzzanese](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [CIDIU S.p.A.](/doc/source/cidiu_it.md) / cidiu.it
- [Contarina S.p.A](/doc/ics/contarina_it.md) / contarina.it
- [Empoli](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Fiesole](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Figline e Incisa Valdarno](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Firenze](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Fucecchio](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Gambassi Terme](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Greve in Chianti](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Il Rifiutologo](/doc/source/ilrifiutologo_it.md) / ilrifiutologo.it
- [Impruneta](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [isontina ambiente: Ronchi dei legionari](/doc/source/isontinambiente_it.md) / isontinambiente.it
- [Lamporecchio](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Larciano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Lastra a Signa](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Marliana](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Massa e Cozzile](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Monsummano Terme](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Montaione](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Montale](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Montecatini Terme](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Montelupo Fiorentino](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Montemurlo](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Montespertoli](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Pescia](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Pieve a Nievole](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Pistoia](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Poggio a Caiano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Ponte Buggianese](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Prato](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Quarrata](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Rignano sull'Arno](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Sambuca Pistoiese](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [San Casciano in Val di Pesa](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [San Marcello Piteglio](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Scandicci](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Scarperia e San Piero](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Serravalle Pistoiese](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Sesto Fiorentino](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Signa](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Uzzano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Vaglia](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Vaiano](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Vernio](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Vicchio](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
- [Vinci](/doc/source/aliaserviziambientali_it.md) / aliaserviziambientali.it
</details>

<details>
<summary>Lithuania</summary>

- [Kauno švara](/doc/source/grafikai_svara_lt.md) / grafikai.svara.lt
- [Telšių keliai](/doc/source/tkeliai_lt.md) / tkeliai.lt
</details>

<details>
<summary>Luxembourg</summary>

- [Esch-sur-Alzette](/doc/source/esch_lu.md) / esch.lu
- [SICA](/doc/source/sica_lu.md) / sica.lu
- [SICA](/doc/source/sicaapp_lu.md) / sicaapp.lu
</details>

<details>
<summary>Netherlands</summary>

- ['s-Hertogenbosch](/doc/source/afvalstoffendienst_nl.md) / afvalstoffendienst.nl
- [ACV Group](/doc/source/ximmio_nl.md) / acv-afvalkalender.nl
- [Afvalstoffendienst.nl](/doc/source/afvalstoffendienst_nl.md) / afvalstoffendienst.nl
- [Alpen an den Rijn](/doc/source/hvcgroep_nl.md) / alphenaandenrijn.nl
- [Altena](/doc/source/afvalstoffendienst_nl.md) / altena.afvalstoffendienstkalender.nl
- [Area Afval](/doc/source/ximmio_nl.md) / area-afval.nl
- [Avalex](/doc/source/ximmio_nl.md) / avalex.nl
- [Avri](/doc/source/ximmio_nl.md) / avri.nl
- [Bar Afvalbeheer](/doc/source/ximmio_nl.md) / bar-afvalbeheer.nl
- [Bernheze](/doc/source/afvalstoffendienst_nl.md) / bernheze.afvalstoffendienstkalender.nl
- [Circulus](/doc/source/circulus_nl.md) / mijn.circulus.nl
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
- [Gemeente Waalre](/doc/source/hvcgroep_nl.md) / waalre.nl
- [Gemeente Westland](/doc/source/ximmio_nl.md) / gemeentewestland.nl
- [Goes](/doc/ics/goes_nl.md) / goes.nl
- [Heusden](/doc/source/afvalstoffendienst_nl.md) / heusden.afvalstoffendienstkalender.nl
- [HVC Groep](/doc/source/hvcgroep_nl.md) / hvcgroep.nl
- [Meerlanden](/doc/source/ximmio_nl.md) / meerlanden.nl
- [Mijn Blink](/doc/source/hvcgroep_nl.md) / mijnblink.nl
- [Oisterwijk](/doc/source/afvalstoffendienst_nl.md) / oisterwijk.afvalstoffendienstkalender.nl
- [PreZero](/doc/source/hvcgroep_nl.md) / prezero.nl
- [Purmerend](/doc/source/hvcgroep_nl.md) / purmerend.nl
- [RAD BV](/doc/source/ximmio_nl.md) / radbv.nl
- [Rd4](/doc/source/rd4_nl.md) / rd4.nl
- [Reinis](/doc/source/ximmio_nl.md) / reinis.nl
- [Spaarnelanden](/doc/source/hvcgroep_nl.md) / spaarnelanden.nl
- [Twente Milieu](/doc/source/ximmio_nl.md) / twentemilieu.nl
- [Vught](/doc/source/afvalstoffendienst_nl.md) / vught.afvalstoffendienstkalender.nl
- [Waardlanden](/doc/source/ximmio_nl.md) / waardlanden.nl
- [Ximmio](/doc/source/ximmio_nl.md) / ximmio.nl
- [ZRD](/doc/source/hvcgroep_nl.md) / zrd.nl
- [Ôffalkalinder van Noardeast-Fryslân & Dantumadiel](/doc/ics/offalkalinder_nl.md) / offalkalinder.nl
</details>

<details>
<summary>New Zealand</summary>

- [Auckland Council](/doc/source/aucklandcouncil_govt_nz.md) / aucklandcouncil.govt.nz
- [Christchurch City Council](/doc/source/ccc_govt_nz.md) / ccc.govt.nz
- [Dunedin District Council](/doc/source/dunedin_govt_nz.md) / dunedin.govt.nz
- [Gore, Invercargill & Southland](/doc/source/wastenet_org_nz.md) / wastenet.org.nz
- [Hamilton City Council](/doc/source/hcc_govt_nz.md) / fightthelandfill.co.nz
- [Horowhenua District Council](/doc/source/horowhenua_govt_nz.md) / horowhenua.govt.nz
- [Hutt City Council](/doc/source/toogoodtowaste_co_nz.md) / toogoodtowaste.co.nz
- [Napier City Council](/doc/source/napier_govt_nz.md) / napier.govt.nz
- [Porirua City](/doc/source/poriruacity_govt_nz.md) / poriruacity.govt.nz
- [Rotorua Lakes Council](/doc/source/rotorua_lakes_council_nz.md) / rotorualakescouncil.nz
- [Tauranga City Council](/doc/source/tauranga_govt_nz.md) / tauranga.govt.nz
- [Waipa District Council](/doc/source/waipa_nz.md) / waipadc.govt.nz
- [Wellington City Council](/doc/source/wellington_govt_nz.md) / wellington.govt.nz
</details>

<details>
<summary>Norway</summary>

- [BIR (Bergensområdets Interkommunale Renovasjonsselskap)](/doc/source/bir_no.md) / bir.no
- [Fosen Renovasjon](/doc/source/fosenrenovasjon_no.md) / fosenrenovasjon.no
- [IRiS](/doc/source/iris_salten_no.md) / iris-salten.no
- [Min Renovasjon](/doc/source/minrenovasjon_no.md) / norkart.no
- [Movar IKS](/doc/source/movar_no.md) / movar.no
- [Oslo Kommune](/doc/source/oslokommune_no.md) / oslo.kommune.no
- [ReMidt Orkland muni](/doc/source/remidt_no.md) / remidt.no
- [Sandnes Kommune](/doc/source/sandnes_no.md) / sandnes.kommune.no
- [Stavanger Kommune](/doc/source/stavanger_no.md) / stavanger.kommune.no
- [Trondheim](/doc/ics/trv_no.md) / trv.no
</details>

<details>
<summary>Poland</summary>

- [App Moje Odpady](/doc/source/moje_odpady_pl.md) / moje-odpady.pl
- [Bydgoszcz Pronatura](/doc/source/pronatura_bydgoszcz_pl.md) / pronatura.bydgoszcz.pl
- [Czerwonak, Murowana Goślina, Oborniki](/doc/source/eko_tom_pl.md) / eko-tom.pl
- [Ecoharmonogram](/doc/source/ecoharmonogram_pl.md) / ecoharmonogram.pl
- [Gmina Miękinia](/doc/source/gmina_miekinia_pl.md) / api.skycms.com.pl
- [Koziegłowy/Objezierze/Oborniki](/doc/source/sepan_remondis_pl.md) / sepan.remondis.pl
- [MPGK Katowice](/doc/source/mpgk_com_pl.md) / mpgk.com.pl
- [Poznań](/doc/source/poznan_pl.md) / poznan.pl/mim/odpady
- [Warsaw](/doc/source/warszawa19115_pl.md) / warszawa19115.pl
- [Wrocław](/doc/source/ekosystem_wroc_pl.md) / ekosystem.wroc.pl
</details>

<details>
<summary>Slovenia</summary>

- [Moji odpadki, Ljubljana](/doc/source/mojiodpadki_si.md) / mojiodpadki.si
</details>

<details>
<summary>Sweden</summary>

- [Affärsverken](/doc/source/affarsverken_se.md) / affarsverken.se
- [Boden](/doc/source/edpevent_se.md) / boden.se
- [Borås Energi och Miljö](/doc/source/edpevent_se.md) / borasem.se
- [EDPEvent - Multi Source](/doc/source/edpevent_se.md) / edpevent.se
- [Gästrike Återvinnare](/doc/source/gastrikeatervinnare_se.md) / gastrikeatervinnare.se
- [Jönköping - June Avfall & Miljö](/doc/source/juneavfall_se.md) / juneavfall.se
- [Kretslopp Sydost](/doc/source/edpevent_se.md) / kretsloppsydost.se
- [Landskrona - Svalövs Renhållning](/doc/source/lsr_nu.md) / lsr.nu
- [Lerum Vatten och Avlopp](/doc/source/lerum_se.md) / vatjanst.lerum.se
- [Linköping - Tekniska Verken](/doc/source/tekniskaverken_se.md) / tekniskaverken.se
- [Luleå](/doc/source/lumire_se.md) / lumire.se
- [Lund Waste Collection](/doc/source/lund_se.md) / eservice431601.lund.se
- [Mölndal](/doc/source/molndal_se.md) / molndal.se
- [Norrtalje Vatten & Avfall](/doc/source/nvaa_se.md) / sjalvservice.nvaa.se
- [North / Middle Bohuslän - Rambo AB](/doc/source/rambo_se.md) / rambo.se
- [Region Gotland](/doc/source/gotland_se.md) / gotland.se
- [Ronneby Miljöteknik](/doc/source/miljoteknik_se.md) / fyrfackronneby.se
- [Roslagsvatten](/doc/source/edpevent_se.md) / roslagsvatten.se
- [Samverkan Återvinning Miljö (SÅM)](/doc/source/samiljo_se.md) / samiljo.se
- [Skellefteå](/doc/source/edpevent_se.md) / skelleftea.se
- [SRV Återvinning](/doc/source/srvatervinning_se.md) / srvatervinning.se
- [SSAM (Deprecated)](/doc/source/ssam_se.md) / ssam.se
- [SSAM Södra Smalånds Avfall & Miljö](/doc/source/edpevent_se.md) / ssam.se
- [Sysav Sophämntning](/doc/source/sysav_se.md) / sysav.se
- [Uppsala Vatten](/doc/source/edpevent_se.md) / uppsalavatten.se
- [Uppsala Vatten och Avfall AB (Deprecated)](/doc/source/uppsalavatten_se.md) / uppsalavatten.se
- [VA Syd Sophämntning](/doc/source/vasyd_se.md) / vasyd.se
- [VIVAB Sophämtning](/doc/source/vivab_se.md) / vivab.se
- [Västervik Miljö & Energi](/doc/source/vmeab_se.md) / vmeab.se
</details>

<details>
<summary>Switzerland</summary>

- [A-Region](/doc/source/a_region_ch.md) / a-region.ch
- [Alchenstorf](/doc/source/alchenstorf_ch.md) / alchenstorf.ch
- [Andwil](/doc/source/a_region_ch.md) / a-region.ch
- [Appenzell](/doc/source/a_region_ch.md) / a-region.ch
- [Berg](/doc/source/a_region_ch.md) / a-region.ch
- [Bühler](/doc/source/a_region_ch.md) / a-region.ch
- [Canton of Zürich](/doc/ics/openerz_metaodi_ch.md) / openerz.metaodi.ch
- [Eggersriet](/doc/source/a_region_ch.md) / a-region.ch
- [Gais](/doc/source/a_region_ch.md) / a-region.ch
- [Gaiserwald](/doc/source/a_region_ch.md) / a-region.ch
- [Gasel](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Goldach](/doc/source/a_region_ch.md) / a-region.ch
- [Grosswangen](/doc/source/grosswangen_ch.md) / grosswangen.ch
- [Grub](/doc/source/a_region_ch.md) / a-region.ch
- [Heiden](/doc/source/a_region_ch.md) / a-region.ch
- [Herisau](/doc/source/a_region_ch.md) / a-region.ch
- [Horn](/doc/source/a_region_ch.md) / a-region.ch
- [Hundwil](/doc/source/a_region_ch.md) / a-region.ch
- [Häggenschwil](/doc/source/a_region_ch.md) / a-region.ch
- [Köniz](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Köniz](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Liebefeld](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Lindau](/doc/source/lindau_ch.md) / lindau.ch
- [Lutzenberg](/doc/source/a_region_ch.md) / a-region.ch
- [Mittelhäusern](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Muolen](/doc/source/a_region_ch.md) / a-region.ch
- [Mörschwil](/doc/source/a_region_ch.md) / a-region.ch
- [Münchenstein](/doc/source/muenchenstein_ch.md) / muenchenstein.ch
- [Münsingen BE, Switzerland](/doc/ics/muensingen_ch.md) / muensingen.ch
- [Nieder-/Oberscherli](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Niederwangen](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Oberwangen](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Rapperswil](/doc/source/rapperswil_be_ch.md) / rapperswil-be.ch
- [Real Luzern](/doc/source/real_luzern_ch.md) / real-luzern.ch
- [Real Luzern](/doc/source/sammelkalender_ch.md) / realluzern.ch
- [Rehetobel](/doc/source/a_region_ch.md) / a-region.ch
- [Rorschach](/doc/source/a_region_ch.md) / a-region.ch
- [Rorschacherberg](/doc/source/a_region_ch.md) / a-region.ch
- [Sammelkalender.ch](/doc/source/sammelkalender_ch.md) / info.sammelkalender.ch
- [Schliern](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Schwellbrunn](/doc/source/a_region_ch.md) / a-region.ch
- [Schönengrund](/doc/source/a_region_ch.md) / a-region.ch
- [Speicher](/doc/source/a_region_ch.md) / a-region.ch
- [Spiegel](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Stadt Bülach](/doc/ics/buelach_ch.md) / buelach.ch
- [Stein](/doc/source/a_region_ch.md) / a-region.ch
- [Steinach](/doc/source/a_region_ch.md) / a-region.ch
- [Teufen](/doc/source/a_region_ch.md) / a-region.ch
- [Thal](/doc/source/a_region_ch.md) / a-region.ch
- [Thörishaus](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Trogen](/doc/source/a_region_ch.md) / a-region.ch
- [Tübach](/doc/source/a_region_ch.md) / a-region.ch
- [Untereggen](/doc/source/a_region_ch.md) / a-region.ch
- [Urnäsch](/doc/source/a_region_ch.md) / a-region.ch
- [Wabern](/doc/source/koeniz_ch.md) / koeniz.citymobile.ch
- [Wald](/doc/source/a_region_ch.md) / a-region.ch
- [Waldkirch](/doc/source/a_region_ch.md) / a-region.ch
- [Waldstatt](/doc/source/a_region_ch.md) / a-region.ch
- [Winterthur](/doc/source/winterthur_ch.md) / winterthur.ch
- [Wittenbach](/doc/source/a_region_ch.md) / a-region.ch
- [Wolfhalden](/doc/source/a_region_ch.md) / a-region.ch
- [ZAKU Entsorgung](/doc/source/sammelkalender_ch.md) / zaku.ch
- [Zeba](/doc/source/sammelkalender_ch.md) / zebazug.ch
- [ZKRI](/doc/source/sammelkalender_ch.md) / zkri.ch
</details>

<details>
<summary>United Kingdom</summary>

- [Aberdeenshire Council](/doc/source/aberdeenshire_gov_uk.md) / aberdeenshire.gov.uk
- [Adur & Worthing Councils](/doc/source/adur_worthing_gov_uk.md) / adur-worthing.gov.uk
- [Allerdale Borough Council](/doc/source/allerdale_gov_uk.md) / allerdale.gov.uk
- [Amber Valley Borough Council](/doc/source/ambervalley_gov_uk.md) / ambervalley.gov.uk
- [Anglesey](/doc/ics/anglesey_gov_wales.md) / anglesey.gov.wales
- [Antrim and Newtownabbey](/doc/source/antrimandnewtownabbey_gov_uk.md) / antrimandnewtownabbey.gov.uk
- [Apps by imactivate](/doc/source/apps_imactivate_com.md) / imactivate.com
- [Ards and North Down Borough Council](/doc/source/ardsandnorthdown_gov_uk.md) / ardsandnorthdown.gov.uk
- [Arun District Council](/doc/source/arun_gov_uk.md) / arun.gov.uk
- [Ashfield District Council](/doc/source/ashfield_gov_uk.md) / ashfield.gov.uk
- [Ashford Borough Council](/doc/source/ashford_gov_uk.md) / ashford.gov.uk
- [Aylesbury Vale District Council](/doc/source/aylesburyvaledc_gov_uk.md) / aylesburyvaledc.gov.uk
- [Barnsley Metropolitan Borough Council](/doc/source/barnsley_gov_uk.md) / barnsley.gov.uk
- [Basildon Council](/doc/source/basildon_gov_uk.md) / basildon.gov.uk
- [Basingstoke and Deane Borough Council](/doc/source/basingstoke_gov_uk.md) / basingstoke.gov.uk
- [Bath & North East Somerset Council](/doc/source/bathnes_gov_uk.md) / bathnes.gov.uk
- [BCP Council](/doc/source/bcp_gov_uk.md) / bcpcouncil.gov.uk
- [Bedford Borough Council](/doc/source/bedford_gov_uk.md) / bedford.gov.uk
- [Binzone](/doc/source/binzone_uk.md) / southoxon.gov.uk
- [Birmingham City Council](/doc/source/birmingham_gov_uk.md) / birmingham.gov.uk
- [Blackburn with Darwen Borough Council](/doc/source/blackburn_gov_uk.md) / blackburn.gov.uk
- [Blackpool Council](/doc/source/blackpool_gov_uk.md) / blackpool.gov.uk
- [Blaenau Gwent County Borough Council](/doc/source/iapp_itouchvision_com.md) / blaenau-gwent.gov.uk
- [Borough Council of King's Lynn & West Norfolk](/doc/source/west_norfolk_gov_uk.md) / west-norfolk.gov.uk
- [Borough of Broxbourne Council](/doc/source/broxbourne_gov_uk.md) / broxbourne.gov.uk
- [Bracknell Forest Council](/doc/source/bracknell_forest_gov_uk.md) / selfservice.mybfc.bracknell-forest.gov.uk
- [Bradford Metropolitan District Council](/doc/source/bradford_gov_uk.md) / bradford.gov.uk
- [Braintree District Council](/doc/source/braintree_gov_uk.md) / braintree.gov.uk
- [Breckland Council](/doc/source/breckland_gov_uk.md) / breckland.gov.uk/mybreckland
- [Brent Council](/doc/ics/brent_gov_uk.md) / brent.gov.uk
- [Bristol City Council](/doc/source/bristol_gov_uk.md) / bristol.gov.uk
- [Broadland District Council](/doc/source/south_norfolk_and_broadland_gov_uk.md) / area.southnorfolkandbroadland.gov.uk
- [Bromsgrove City Council](/doc/source/bromsgrove_gov_uk.md) / bromsgrove.gov.uk
- [Broxtowe Borough Council](/doc/source/broxtowe_gov_uk.md) / broxtowe.gov.uk
- [Buckinghamshire: Former (Chiltern, South Bucks, Wycombe)](/doc/source/iapp_itouchvision_com.md) / buckinghamshire.gov.uk
- [Burnley Council](/doc/source/burnley_gov_uk.md) / burnley.gov.uk
- [Bury Council](/doc/source/bury_gov_uk.md) / bury.gov.uk
- [Cambridge City Council](/doc/source/cambridge_gov_uk.md) / cambridge.gov.uk
- [Canterbury City Council](/doc/source/canterbury_gov_uk.md) / canterbury.gov.uk
- [Cardiff Council](/doc/source/cardiff_gov_uk.md) / cardiff.gov.uk
- [Carmarthenshire County Council](/doc/source/carmarthenshire_gov_wales.md) / carmarthenshire.gov.wales
- [Central Bedfordshire Council](/doc/source/centralbedfordshire_gov_uk.md) / centralbedfordshire.gov.uk
- [Charnwood](/doc/source/charnwood_gov_uk.md) / charnwood.gov.uk
- [Cherwell District Council](/doc/source/cherwell_gov_uk.md) / cherwell.gov.uk
- [Cheshire East Council](/doc/source/cheshire_east_gov_uk.md) / cheshireeast.gov.uk
- [Cheshire West and Chester Council](/doc/source/cheshire_west_and_chester_gov_uk.md) / cheshirewestandchester.gov.uk
- [Chesterfield Borough Council](/doc/source/chesterfield_gov_uk.md) / chesterfield.gov.uk
- [Chichester District Council](/doc/source/chichester_gov_uk.md) / chichester.gov.uk
- [City of Doncaster Council](/doc/source/doncaster_gov_uk.md) / doncaster.gov.uk
- [City Of Lincoln Council](/doc/source/lincoln_gov_uk.md) / lincoln.gov.uk
- [City of York Council](/doc/source/york_gov_uk.md) / york.gov.uk
- [Colchester City Council](/doc/source/colchester_gov_uk.md) / colchester.gov.uk
- [Conwy County Borough Council](/doc/source/conwy_gov_uk.md) / conwy.gov.uk
- [Cornwall Council](/doc/source/cornwall_gov_uk.md) / cornwall.gov.uk
- [Crawley Borough Council (myCrawley)](/doc/source/crawley_gov_uk.md) / crawley.gov.uk
- [Croydon Council](/doc/source/croydon_gov_uk.md) / croydon.gov.uk
- [Darlington Borough Council](/doc/source/darlington_gov_uk.md) / darlington.gov.uk
- [Denbighshire County Council](/doc/source/denbighshire_gov_uk.md) / denbighshire.gov.uk
- [Deprecated: Buckinghamshire](/doc/source/chiltern_gov_uk.md) / chiltern.gov.uk
- [Derby City Council](/doc/source/derby_gov_uk.md) / derby.gov.uk
- [Dorset Council](/doc/source/dorset_gov_uk.md) / dorsetcouncil.gov.uk
- [Dover District Council](/doc/source/dover_gov_uk.md) / dover.gov.uk
- [Dudley Metropolitan Borough Council](/doc/source/dudley_gov_uk.md) / dudley.gov.uk
- [Dundee City Council](/doc/source/dundeecity_gov_uk.md) / dundeecity.gov.uk
- [Dundee MyBins](/doc/source/dundeecity_gov_uk.md) / dundee-mybins.co.uk
- [Durham County Council](/doc/source/durham_gov_uk.md) / durham.gov.uk
- [East Ayrshire Council](/doc/source/east_ayrshire_gov_uk.md) / east-ayrshire.gov.uk
- [East Cambridgeshire District Council](/doc/source/eastcambs_gov_uk.md) / eastcambs.gov.uk
- [East Devon District Council](/doc/source/eastdevon_gov_uk.md) / eastdevon.gov.uk
- [East Herts Council](/doc/source/eastherts_gov_uk.md) / eastherts.gov.uk
- [East Lothian](/doc/source/eastlothian_gov_uk.md) / eastlothian.gov.uk
- [East Northamptonshire and Wellingborough](/doc/source/east_northamptonshire_gov_uk.md) / east-northamptonshire.gov.uk
- [East Renfrewshire Council](/doc/source/east_renfrewshire_gov_uk.md) / eastrenfrewshire.gov.uk
- [East Riding of Yorkshire Council](/doc/source/eastriding_gov_uk.md) / eastriding.gov.uk
- [Eastbourne Borough Council](/doc/source/environmentfirst_co_uk.md) / lewes-eastbourne.gov.uk
- [Eastleigh Borough Council](/doc/source/eastleigh_gov_uk.md) / eastleigh.gov.uk
- [Elmbridge Borough Council](/doc/source/elmbridge_gov_uk.md) / elmbridge.gov.uk
- [Environment First](/doc/source/environmentfirst_co_uk.md) / environmentfirst.co.uk
- [Exeter City Council](/doc/source/exeter_gov_uk.md) / exeter.gov.uk
- [Falkirk](/doc/ics/falkirk_gov_uk.md) / falkirk.gov.uk
- [Fareham Borough Council](/doc/source/fareham_gov_uk.md) / fareham.gov.uk
- [FCC Environment](/doc/source/fccenvironment_co_uk.md) / fccenvironment.co.uk
- [Fenland](/doc/source/apps_imactivate_com.md) / fenland.gov.uk
- [Fenland District Council](/doc/source/fenland_gov_uk.md) / fenland.gov.uk
- [Fife Council](/doc/source/fife_gov_uk.md) / fife.gov.uk
- [Flintshire](/doc/source/flintshire_gov_uk.md) / flintshire.gov.uk
- [Fylde Council](/doc/source/fylde_gov_uk.md) / fylde.gov.uk
- [Gateshead Council](/doc/source/gateshead_gov_uk.md) / gateshead.gov.uk
- [Gedling Borough Council (unofficial)](/doc/ics/gedling_gov_uk.md) / gbcbincalendars.co.uk
- [Glasgow City Council](/doc/source/glasgow_gov_uk.md) / glasgow.gov.uk
- [Guildford Borough Council](/doc/source/guildford_gov_uk.md) / guildford.gov.uk
- [Gwynedd](/doc/source/gwynedd_gov_uk.md) / gwynedd.gov.uk
- [Harborough District Council](/doc/source/fccenvironment_co_uk.md) / harborough.gov.uk
- [Haringey Council](/doc/source/haringey_gov_uk.md) / haringey.gov.uk
- [Harlow Council](/doc/source/harlow_gov_uk.md) / harlow.gov.uk
- [Hart District Council](/doc/source/hart_gov_uk.md) / hart.gov.uk
- [Herefordshire City Council](/doc/source/herefordshire_gov_uk.md) / herefordshire.gov.uk
- [High Peak Borough Council](/doc/source/highpeak_gov_uk.md) / highpeak.gov.uk
- [Highland](/doc/source/highland_gov_uk.md) / highland.gov.uk
- [Horsham District Council](/doc/source/horsham_gov_uk.md) / horsham.gov.uk
- [Hull City Council](/doc/source/hull_gov_uk.md) / hull.gov.uk
- [Huntingdonshire District Council](/doc/source/huntingdonshire_gov_uk.md) / huntingdonshire.gov.uk
- [Islington Council](/doc/source/islington_gov_uk.md) / islington.gov.uk
- [iTouchVision](/doc/source/iweb_itouchvision_com.md) / iweb.itouchvision.com
- [Itouchvision Source using the encrypted API](/doc/source/iapp_itouchvision_com.md) / itouchvision.com
- [Joint Waste Solutions](/doc/source/jointwastesolutions_org.md) / jointwastesolutions.org
- [Kirklees Council](/doc/source/kirklees_gov_uk.md) / kirklees.gov.uk
- [Lancaster City Council](/doc/source/lancaster_gov_uk.md) / lancaster.gov.uk
- [Leeds](/doc/source/apps_imactivate_com.md) / leeds.gov.uk
- [Leicester City Council](/doc/source/biffaleicester_co_uk.md) / leicester.gov.uk
- [Lewes District Council](/doc/source/environmentfirst_co_uk.md) / lewes-eastbourne.gov.uk
- [Lichfield District Council](/doc/source/lichfielddc_gov_uk.md) / lichfielddc.gov.uk
- [Lisburn and Castlereagh City Council](/doc/source/lisburn_castlereagh_gov_uk.md) / lisburncastlereagh.gov.uk
- [Liverpool City Council](/doc/source/liverpool_gov_uk.md) / liverpool.gov.uk
- [London Borough of Barking and Dagenham](/doc/source/lbbd_gov_uk.md) / lbbd.gov.uk
- [London Borough of Bexley](/doc/source/bexley_gov_uk.md) / bexley.gov.uk
- [London Borough of Bromley](/doc/source/bromley_gov_uk.md) / bromley.gov.uk
- [London Borough of Camden](/doc/source/camden_gov_uk.md) / camden.gov.uk
- [London Borough of Harrow](/doc/source/harrow_gov_uk.md) / harrow.gov.uk
- [London Borough of Hounslow](/doc/source/hounslow_gov_uk.md) / hounslow.gov.uk
- [London Borough of Lewisham](/doc/source/lewisham_gov_uk.md) / lewisham.gov.uk
- [London Borough of Merton](/doc/source/merton_gov_uk.md) / merton.gov.uk
- [London Borough of Newham](/doc/source/newham_gov_uk.md) / newham.gov.uk
- [Luton](/doc/source/apps_imactivate_com.md) / luton.gov.uk
- [Maidstone Borough Council](/doc/source/maidstone_gov_uk.md) / maidstone.gov.uk
- [Maldon District Council](/doc/source/maldon_gov_uk.md) / maldon.gov.uk
- [Malvern Hills](/doc/source/roundlookup_uk.md) / malvernhills.gov.uk
- [Malvern Hills District Council](/doc/source/roundlookup_uk.md) / malvernhills.gov.uk
- [Manchester City Council](/doc/source/manchester_uk.md) / manchester.gov.uk
- [Mansfield District Council](/doc/source/mansfield_gov_uk.md) / mansfield.gov.uk
- [Mendip District Council](/doc/source/iweb_itouchvision_com.md) / somerset.gov.uk
- [Mid-Sussex District Council](/doc/source/midsussex_gov_uk.md) / midsussex.gov.uk
- [Middlesbrough Council](/doc/ics/recollect.md) / middlesbrough.gov.uk
- [Milton Keynes council](/doc/source/milton_keynes_gov_uk.md) / milton-keynes.gov.uk
- [Moray Council](/doc/source/moray_gov_uk.md) / moray.gov.uk
- [Newark & Sherwood District Council](/doc/source/newark_sherwooddc_gov_uk.md) / newark-sherwooddc.gov.uk
- [Newcastle City Council](/doc/source/newcastle_gov_uk.md) / community.newcastle.gov.uk
- [Newcastle Under Lyme Borough Council](/doc/source/newcastle_staffs_gov_uk.md) / newcastle-staffs.gov.uk
- [Newport City Council](/doc/source/iapp_itouchvision_com.md) / newport.gov.uk
- [Newport City Council](/doc/source/iweb_itouchvision_com.md) / newport.gov.uk/
- [North Ayrshire Council](/doc/source/north_ayrshire_gov_uk.md) / north-ayrshire.gov.uk
- [North Herts Council](/doc/source/northherts_gov_uk.md) / north-herts.gov.uk
- [North Kesteven District Council](/doc/source/north_kesteven_org_uk.md) / n-kesteven.org.uk
- [North Lincolnshire Council](/doc/source/northlincs_gov_uk.md) / northlincs.gov.uk
- [North Northamptonshire council](/doc/source/northnorthants_gov_uk.md) / northnorthants.gov.uk
- [North Somerset Council](/doc/source/nsomerset_gov_uk.md) / n-somerset.gov.uk
- [North West Leicestershire District Council](/doc/source/nwleics_gov_uk.md) / nwleics.gov.uk
- [North Yorkshire Council - Hambleton](/doc/source/northyorks_hambleton_gov_uk.md) / northyorks.gov.uk
- [North Yorkshire Council - Harrogate](/doc/source/northyorks_harrogate_gov_uk.md) / secure.harrogate.gov.uk
- [North Yorkshire Council - Scarborough](/doc/source/northyorks_scarborough_gov_uk.md) / northyorks.gov.uk
- [North Yorkshire Council - Selby](/doc/source/northyorks_selby_gov_uk.md) / northyorks.gov.uk
- [Nottingham City Council](/doc/source/nottingham_city_gov_uk.md) / nottinghamcity.gov.uk
- [Oadby and Wigston Council](/doc/source/oadby_wigston_gov_uk.md) / oadby-wigston.gov.uk
- [Oxford City Council](/doc/source/oxford_gov_uk.md) / oxford.gov.uk
- [Peterborough City Council](/doc/source/peterborough_gov_uk.md) / peterborough.gov.uk
- [Portsmouth City Council](/doc/source/portsmouth_gov_uk.md) / portsmouth.gov.uk
- [Reading Council](/doc/source/reading_gov_uk.md) / reading.gov.uk
- [Redbridge Council](/doc/source/redbridge_gov_uk.md) / redbridge.gov.uk
- [Reigate & Banstead Borough Council](/doc/source/reigatebanstead_gov_uk.md) / reigate-banstead.gov.uk
- [Renfrewshire Council](/doc/source/renfrewshire_gov_uk.md) / renfrewshire.gov.uk
- [Rhondda Cynon Taf County Borough Council](/doc/source/rctcbc_gov_uk.md) / rctcbc.gov.uk
- [Richmondshire District Council](/doc/source/richmondshire_gov_uk.md) / richmondshire.gov.uk
- [Rotherham](/doc/source/apps_imactivate_com.md) / rotherham.gov.uk
- [Rotherham Metropolitan Borough Council](/doc/source/rotherham_gov_uk.md) / rotherham.gov.uk
- [Runnymede Borough Council](/doc/source/runnymede_gov_uk.md) / runnymede.gov.uk
- [Rushcliffe Brough Council](/doc/source/rushcliffe_gov_uk.md) / rushcliffe.gov.uk
- [Rushmoor Borough Council](/doc/source/rushmoor_gov_uk.md) / rushmoor.gov.uk
- [Salford City Council](/doc/source/salford_gov_uk.md) / salford.gov.uk
- [Sedgemoor District Council](/doc/source/iweb_itouchvision_com.md) / somerset.gov.uk
- [Sheffield City Council](/doc/source/sheffield_gov_uk.md) / sheffield.gov.uk
- [Shropshire Council](/doc/source/shropshire_gov_uk.md) / shropshire.gov.uk
- [Solihull Council](/doc/source/solihull_gov_uk.md) / denbighshire.gov.uk
- [Somerset Council](/doc/source/iweb_itouchvision_com.md) / somerset.gov.uk
- [Somerset County Council](/doc/source/iweb_itouchvision_com.md) / somerset.gov.uk
- [Somerset West & Taunton District Council](/doc/source/iweb_itouchvision_com.md) / somerset.gov.uk
- [South Cambridgeshire District Council](/doc/source/scambs_gov_uk.md) / scambs.gov.uk
- [South Derbyshire District Council](/doc/source/southderbyshire_gov_uk.md) / southderbyshire.gov.uk
- [South Gloucestershire Council](/doc/source/southglos_gov_uk.md) / southglos.gov.uk
- [South Hams District Council](/doc/source/fccenvironment_co_uk.md) / southhams.gov.uk
- [South Holland District Council](/doc/source/sholland_gov_uk.md) / sholland.gov.uk
- [South Kesteven District Council](/doc/source/southkesteven_gov_uk.md) / southkesteven.gov.uk
- [South Norfolk Council](/doc/source/south_norfolk_and_broadland_gov_uk.md) / southnorfolkandbroadland.gov.uk
- [South Oxfordshire District Council](/doc/source/binzone_uk.md) / southoxon.gov.uk
- [South Somerset District Council](/doc/source/iweb_itouchvision_com.md) / somerset.gov.uk
- [South Tyneside Council](/doc/source/southtyneside_gov_uk.md) / southtyneside.gov.uk
- [Southampton City Council](/doc/source/southampton_gov_uk.md) / southampton.gov.uk
- [St Albans City & District Council](/doc/source/stalbans_gov_uk.md) / stalbans.gov.uk
- [Stafford Borough Council](/doc/source/staffordbc_gov_uk.md) / staffordbc.gov.uk
- [Stevenage Borough Council](/doc/source/stevenage_gov_uk.md) / stevenage.gov.uk
- [Stirling.gov.uk](/doc/source/stirling_uk.md) / stirling.gov.uk
- [Stockport Council](/doc/source/stockport_gov_uk.md) / stockport.gov.uk
- [Stockton-on-Tees Borough Council](/doc/source/stockton_gov_uk.md) / stockton.gov.uk
- [Stoke-on-Trent](/doc/source/stoke_gov_uk.md) / stoke.gov.uk
- [Stratford District Council](/doc/source/stratford_gov_uk.md) / stratford.gov.uk
- [Stroud District Council](/doc/source/stroud_gov_uk.md) / stroud.gov.uk
- [Surrey Heath Borough Council](/doc/source/jointwastesolutions_org.md) / surreyheath.gov.uk
- [Sutton Council, London](/doc/source/sutton_gov_uk.md) / sutton.gov.uk
- [Swansea Council](/doc/source/swansea_gov_uk.md) / swansea.gov.uk
- [Swindon Borough Council](/doc/source/swindon_gov_uk.md) / swindon.gov.uk
- [Tameside Metropolitan Borough Council](/doc/source/tameside_gov_uk.md) / tameside.gov.uk
- [Telford and Wrekin Council](/doc/source/telford_gov_uk.md) / telford.gov.uk
- [Test Valley Borough Council](/doc/source/iweb_itouchvision_com.md) / testvalley.gov.uk
- [Tewkesbury Borough Council](/doc/source/tewkesbury_gov_uk.md) / tewkesbury.gov.uk
- [The Royal Borough of Kingston Council](/doc/source/kingston_gov_uk.md) / kingston.gov.uk
- [Tonbridge and Malling Borough Council](/doc/source/tmbc_gov_uk.md) / tmbc.gov.uk
- [Tunbridge Wells](/doc/source/tunbridgewells_gov_uk.md) / tunbridgewells.gov.uk
- [UK Bin Collection Schedule (UKBCD) project](/doc/source/ukbcd.md) / github.com/robbrad/UKBinCollectionData
- [Uttlesford District Council](/doc/source/uttlesford_gov_uk.md) / uttlesford.gov.uk
- [Vale of Glamorgan Council](/doc/source/valeofglamorgan_gov_uk.md) / valeofglamorgan.gov.uk
- [Vale of White Horse District Council](/doc/source/binzone_uk.md) / whitehorsedc.gov.uk
- [Walsall Council](/doc/source/walsall_gov_uk.md) / walsall.gov.uk
- [Warrington Borough Council](/doc/source/warrington_gov_uk.md) / warrington.gov.uk
- [Warwick District Council](/doc/source/warwickdc_gov_uk.md) / warwickdc.gov.uk
- [Waverley Borough Council](/doc/source/waverley_gov_uk.md) / waverley.gov.uk
- [Wealden District Council](/doc/source/wealden_gov_uk.md) / wealden.gov.uk
- [Welwyn Hatfield Borough Council](/doc/source/welhat_gov_uk.md) / welhat.gov.uk
- [West Berkshire Council](/doc/source/westberks_gov_uk.md) / westberks.gov.uk
- [West Devon Borough Council](/doc/source/fccenvironment_co_uk.md) / westdevon.gov.uk
- [West Dunbartonshire Council](/doc/source/west_dunbartonshire_gov_uk.md) / west-dunbarton.gov.uk
- [West Northamptonshire council](/doc/source/westnorthants_gov_uk.md) / westnorthants.gov.uk
- [West Oxfordshire District Council](/doc/source/westoxon_gov_uk.md) / westoxon.gov.uk
- [West Suffolk Council](/doc/source/westsuffolk_gov_uk.md) / westsuffolk.gov.uk
- [Westmorland & Furness Council, Barrow area](/doc/ics/barrowbc_gov_uk.md) / barrowbc.gov.uk
- [Westmorland & Furness Council, South Lakeland area](/doc/ics/southlakeland_gov_uk.md) / southlakeland.gov.uk
- [Wigan Council](/doc/source/wigan_gov_uk.md) / wigan.gov.uk
- [Wiltshire Council](/doc/source/wiltshire_gov_uk.md) / wiltshire.gov.uk
- [Windsor and Maidenhead](/doc/source/rbwm_gov_uk.md) / my.rbwm.gov.uk
- [Wirral Council](/doc/source/wirral_gov_uk.md) / wirral.gov.uk
- [Woking Borough Council](/doc/source/jointwastesolutions_org.md) / woking.gov.uk
- [Wokingham Borough Council](/doc/source/wokingham_gov_uk.md) / wokingham.gov.uk
- [Worcester City](/doc/source/roundlookup_uk.md) / worcester.gov.uk
- [Wychavon](/doc/source/roundlookup_uk.md) / wychavon.gov.uk
- [Wychavon District Council (Deprecated)](/doc/source/wychavon_gov_uk.md) / wychavon.gov.uk
- [Wyre Borough Council](/doc/source/wyre_gov_uk.md) / wyre.gov.uk
- [Wyre Forest District Council](/doc/source/wyreforestdc_gov_uk.md) / wyreforestdc.gov.uk
</details>

<details>
<summary>United States of America</summary>

- [Albuquerque, New Mexico, USA](/doc/source/recyclecoach_com.md) / recyclecoach.com/cities/usa-nm-city-of-albuquerque
- [City of Austin, TX](/doc/ics/recollect.md) / austintexas.gov
- [City of Bloomington](/doc/ics/recollect.md) / bloomington.in.gov
- [City of Cambridge](/doc/ics/recollect.md) / cambridgema.gov
- [City of Gastonia, NC](/doc/ics/recollect.md) / gastonianc.gov
- [City of Georgetown, TX](/doc/ics/recollect.md) / texasdisposal.com/waste-wizard
- [City of McKinney, TX](/doc/ics/recollect.md) / mckinneytexas.org
- [City of Oklahoma City (unofficial)](/doc/source/okc_gov.md) / okc.gov
- [City of Pittsburgh](/doc/source/pgh_st.md) / pgh.st
- [Louisville, Kentucky, USA](/doc/source/recyclecoach_com.md) / recyclecoach.com/cities/usa-ky-city-of-louisville
- [New York City](/doc/source/nyc_gov.md) / nyc.gov
- [Newark, Delaware, USA](/doc/source/recyclecoach_com.md) / recyclecoach.com/cities/usa-de-city-of-newark
- [Olympia, Washington, USA](/doc/source/recyclecoach_com.md) / recyclecoach.com/cities/usa-wa-city-of-olympia
- [ReCollect](/doc/ics/recollect.md) / recollect.net
- [Recycle Coach](/doc/source/recyclecoach_com.md) / recyclecoach.com
- [Republic Services](/doc/source/republicservices_com.md) / republicservices.com
- [Seattle Public Utilities](/doc/source/seattle_gov.md) / myutilities.seattle.gov
- [Tucson, Arizona, USA](/doc/source/recyclecoach_com.md) / recyclecoach.com/cities/usa-az-city-of-tucson
- [University Park, TX](/doc/ics/recollect.md) / uptexas.org
- [Waste Connections](/doc/ics/recollect.md) / wasteconnections.com
</details>

<!--End of country section-->

---

# Installation

![hacs badge](https://img.shields.io/badge/HACS-Default-orange)
![hacs installs](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fwaste_collection_schedule)

Waste Collection Schedule can be installed via [HACS](https://hacs.xyz/), or by manually copying the [`waste_collection_schedule`](https://github.com/mampfes/hacs_waste_collection_schedule/tree/master/custom_components) directory to Home Assistant's `config/custom_components/` directory.

# Configuration

This integration can be configured through the Home Assistant UI. From the Devices & Services page click 'Add Integration' and search for 'Waste Collection Schedule'.

Alternatively, Waste Collection Schedule can be configured manually in the yaml configuration files. This is required for certain advanced options.
For further details see the [installation and configuration](/doc/installation.md) page, or the [FAQ](/doc/faq.md).

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

For further details see [contributing](/doc/contributing.md) guidelines, or take a look at our [online](/doc/online.md) mentions.

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

**Solution:** Try to reinstall Waste Collection Schedule (if you are using HACS) or install the required Python packages manually. This list of required packages can be found in [manifest.json](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/manifest.json#L9).

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

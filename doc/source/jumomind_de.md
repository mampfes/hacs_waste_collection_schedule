# Jumomind.de / MyMuell.de

Support for schedules provided by [jumomind.de](https://jumomind.de/) and [MyMüll App](https://www.mymuell.de). Jumomind and MyMüll are services provided by [junker.digital](https://junker.digital/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: SERVICE_ID
        city: CITY
        street: STREET
        house_number: HOUSE NUMBER
        city_id: CITY_ID # deprecated
        area_id: AREA_ID # deprecated
```

### Configuration Variables

**service_id**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(string) (optional)*  
Not needed for all providers or cities

**house_number**  
*(string) (optional)*  
Not needed for all providers, cities or streets

**city_id**  
*(string) (optional)* (deprecated)*

**area_id**  
*(string) (required)* (deprecated)*

## Example

### ZAW

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: zaw
        city: Alsbach-Hähnlein
        street: Hauptstr.
```

### MyMuell

#### Without street

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: mymuell
        city: Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf
```

#### With street

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: mymuell
        city: Darmstadt
        street: Adolf-Spieß-Straße 2-8 # Housenumber is part of street so it is not in house_number
```

### Deprecated

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: zaw
        city_id: 106
        area_id: 94
```

## How to get the source arguments

### Table source_id and its cities

|service_id|cities|
|---|---|
|zaw|`Alsbach-Hähnlein`,`Babenhausen`,`Bickenbach`,`Dieburg`,`Eppertshausen`,`Erzhausen`,`Fischbachtal`,`Griesheim`,`Groß-Bieberau`,`Groß-Umstadt`,`Groß-Zimmern`,`Messel`,`Modautal`,`Mühltal`,`Münster`,`Ober-Ramstadt`,`Otzberg`,`Pfungstadt`,`Reinheim`,`Roßdorf`,`Schaafheim`,`Seeheim-Jugenheim`,`Weiterstadt`,|
|ingol|`Ingolstadt`,|
|aoe|`Altötting`,`Burghausen`,`Burgkirchen`,`Emmerting`,`Erlbach`,`Feichten`,`Garching`,`Haiming`,`Halsbach`,`Kastl`,`Kirchweidach`,`Marktl`,`Mehring`,`Neuötting`,`Perach`,`Pleiskirchen`,`Reischach`,`Stammham`,`Teising`,`Töging am Inn`,`Tüßling`,`Tyrlaching`,`Unterneukirchen`,`Winhöring`,|
|lka|`Aurich`,`Baltrum`,`Brookmerland`,`Dornum`,`Großefehn`,`Großheide`,`Hage`,`Hinte`,`Ihlow`,`Juist`,`Krummhörn`,`Norden`,`Norderney`,`Südbrookmerland`,`Wiesmoor`,|
|hom|`Bad Homburg`,|
|bdg|`Ahrensfelde-Ahrensfelde`,`Ahrensfelde-Blumberg`,`Ahrensfelde-Eiche`,`Ahrensfelde-Lindenberg`,`Ahrensfelde-Mehrow`,`Althüttendorf-Althüttendorf`,`Althüttendorf-Neugrimnitz`,`Bernau bei Berlin-Bernau bei Berlin`,`Bernau bei Berlin-Birkenhöhe`,`Bernau bei Berlin-Birkholz`,`Bernau bei Berlin-Birkholzaue`,`Bernau bei Berlin-Börnicke`,`Bernau bei Berlin-Ladeburg`,`Bernau bei Berlin-Lobetal`,`Bernau bei Berlin-Schönow`,`Bernau bei Berlin-Waldfrieden`,`Bernau bei Berlin-Waldsiedlung`,`Biesenthal-Biesenthal`,`Biesenthal-Danewitz`,`Breydin-Trampe`,`Breydin-Tuchen-Klobbicke`,`Britz-Britz`,`Chorin-Brodowin`,`Chorin-Chorin`,`Chorin-Golzow`,`Chorin-Neuehütte`,`Chorin-Sandkrug`,`Chorin-Senftenhütte`,`Chorin-Serwest`,`Eberswalde-Eberswalde`,`Eberswalde-Sommerfelde`,`Eberswalde-Sommerfelde-Ausbau`,`Eberswalde-Spechthausen`,`Eberswalde-Tornow`,`Friedrichswalde-Friedrichswalde`,`Friedrichswalde-Parlow-Glambeck`,`Hohenfinow-Hohenfinow`,`Joachimsthal-Joachimsthal`,`Liepe-Liepe`,`Lunow-Stolzenhagen-Lunow`,`Lunow-Stolzenhagen-Stolzenhagen`,`Marienwerder-Marienwerder`,`Marienwerder-Ruhlsdorf`,`Marienwerder-Sophienstädt`,`Melchow-Melchow`,`Melchow-Schönholz`,`Niederfinow-Niederfinow`,`Oderberg-Oderberg`,`Panketal-Schwanebeck`,`Panketal-Zepernick`,`Parsteinsee-Lüdersdorf`,`Parsteinsee-Parstein`,`Rüdnitz-Rüdnitz`,`Schorfheide-Altenhof`,`Schorfheide-Böhmerheide`,`Schorfheide-Eichhorst`,`Schorfheide-Finowfurt`,`Schorfheide-Groß Schönebeck`,`Schorfheide-Klandorf`,`Schorfheide-Lichterfelde`,`Schorfheide-Schluft`,`Schorfheide-Werbellin`,`Sydower Fließ-Grüntal`,`Sydower Fließ-Tempelfelde`,`Wandlitz-Basdorf`,`Wandlitz-Klosterfelde`,`Wandlitz-Lanke`,`Wandlitz-Prenden`,`Wandlitz-Schönerlinde`,`Wandlitz-Schönwalde`,`Wandlitz-Stolzenhagen`,`Wandlitz-Wandlitz`,`Wandlitz-Zerpenschleuse`,`Werneuchen-Hirschfelde`,`Werneuchen-Krummensee`,`Werneuchen-Löhme`,`Werneuchen-Schönfeld`,`Werneuchen-Seefeld`,`Werneuchen-Tiefensee`,`Werneuchen-Weesow`,`Werneuchen-Werneuchen`,`Werneuchen-Willmersdorf`,`Ziethen-Groß Ziethen`,`Ziethen-Klein Ziethen`,|
|hat|`Hattersheim`,|
|lue|`Alswede`,`Blasheim`,`Eilhausen`,`Gehlenbeck`,`Lübbecke`,`Nettelstedt`,`Obermehnen`,`Stockhausen`,|
|sbm|`Minden`,|
|ksr|`Recklinghausen`,|
|rhe|`Alterkülz`,`Altweidelbach`,`Argenthal`,`Außerhalb Landkreis`,`Bacharach`,`Bad Kreuznach`,`Badenhard`,`Bärenbach`,`Belg`,`Belgweiler`,`Bell`,`Beltheim`,`Benzweiler`,`Bergenhausen`,`Beulich`,`Bickenbach`,`Biebern`,`Birkheim`,`Boppard`,`Braunshorn`,`Bubach`,`Buch`,`Büchenbeuren`,`Budenbach`,`Damscheid`,`Dichtelbach`,`Dickenschied`,`Dill`,`Dillendorf`,`Dommershausen`,`Dörth`,`Ellern`,`Emmelshausen`,`Erbach`,`Fronhofen`,`Gehlweiler`,`Gemünden`,`Gödenroth`,`Gondershausen`,`Hahn`,`Halsenbach`,`Hasselbach`,`Hausbay`,`Hecken`,`Heinzenbach`,`Henau`,`Hirschfeld`,`Hollnich`,`Holzbach`,`Horn`,`Hungenroth`,`Kappel`,`Karbach`,`Kastellaun`,`Keidelheim`,`Kirchberg`,`Kisselbach`,`Klosterkumbd`,`Kludenbach`,`Korweiler`,`Kratzenburg`,`Külz`,`Kümbdchen`,`Lahr`,`Laubach`,`Laudert`,`Laufersweiler`,`Lautzenhausen`,`Leiningen`,`Liebshausen`,`Lindenschied`,`Lingerhahn`,`Linkenbach`,`Maisborn`,`Maitzborn`,`Mastershausen`,`Mengerschied`,`Mermuth`,`Metzenhausen`,`Michelbach`,`Mörschbach`,`Mörsdorf`,`Morshausen`,`Mühlpfad`,`Mutterschied`,`Nannhausen`,`Neuerkirch`,`Ney`,`Niederburg`,`Niederkostenz`,`Niederkumbd`,`Niedersohren`,`Niedert`,`Niederweiler`,`Norath`,`Oberkostenz`,`Oberwesel`,`Ohlweiler`,`Oppertshausen`,`Perscheid`,`Pfalzfeld`,`Pleizenhausen`,`Ravengiersburg`,`Raversbeuren`,`Rayerschied`,`Reckershausen`,`Reich`,`Rheinböllen`,`Riegenroth`,`Riesweiler`,`Rödelhausen`,`Rödern`,`Rohrbach`,`Roth`,`Sargenroth`,`Schlierschied`,`Schnorbach`,`Schönborn`,`Schwall`,`Schwarzen`,`Simmern`,`Sohren`,`Sohrschied`,`Spesenroth`,`St. Goar`,`Steinbach`,`Thörlingen`,`Tiefenbach`,`Todenroth`,`Uhler`,`Unzenberg`,`Urbar`,`Utzenhain`,`Wahlbach`,`Wahlenau`,`Wiebelsheim`,`Womrath`,`Woppenroth`,`Würrich`,`Wüschheim`,`Zilshausen`,|
|udg|`Angermünde`,`Angermünde - Altkünkendorf`,`Angermünde - Biesenbrow`,`Angermünde - Bölkendorf`,`Angermünde - Bruchhagen`,`Angermünde - Crussow`,`Angermünde - Dobberzin`,`Angermünde - Frauenhagen`,`Angermünde - Friedrichsfelde`,`Angermünde - Gellmersdorf`,`Angermünde - Görlsdorf`,`Angermünde - Greiffenberg`,`Angermünde - Günterberg`,`Angermünde - Henriettenhof`,`Angermünde - Herzsprung`,`Angermünde - Kerkow`,`Angermünde - Leopoldsthal`,`Angermünde - Louisenhof`,`Angermünde - Mürow`,`Angermünde - Neuhof`,`Angermünde - Neukünkendorf`,`Angermünde - Schmargendorf`,`Angermünde - Schmiedeberg`,`Angermünde - Steinhöfel`,`Angermünde - Sternfelde`,`Angermünde - Stolpe`,`Angermünde - Welsow`,`Angermünde - Wilmersdorf`,`Angermünde - Wolletz`,`Angermünde - Zuchenberg`,`Boitzenburger Land - Berkholz`,`Boitzenburger Land - Boitzenburg`,`Boitzenburger Land - Buchenhain`,`Boitzenburger Land - Funkenhagen`,`Boitzenburger Land - Hardenbeck`,`Boitzenburger Land - Haßleben`,`Boitzenburger Land - Jakobshagen`,`Boitzenburger Land - Klaushagen`,`Boitzenburger Land - Warthe`,`Boitzenburger Land - Wichmannsdorf`,`Brüssow`,`Carmzow-Wallmow`,`Casekow`,`Casekow - Biesendahlshof`,`Casekow - Blumberg`,`Casekow - Luckow`,`Casekow - Petershagen`,`Casekow - Wartin`,`Casekow - Woltersdorf`,`Flieth-Stegelitz - Flieth`,`Flieth-Stegelitz - Stegelitz`,`Gartz (Oder)`,`Gartz (Oder) - Friedrichsthal`,`Gartz (Oder) - Geesow`,`Gartz (Oder) - Hohenreinkendorf`,`Gerswalde`,`Göritz`,`Gramzow`,`Gramzow - Lützlow`,`Gramzow - Meichow`,`Gramzow - Neu-Meichow`,`Gramzow - Polßen`,`Grünow`,`Grünow - Damme`,`Grünow - Drense`,`Grünow - Heiseshof`,`Hohenselchow-Groß Pinnow`,`Hohenselchow-Groß Pinnow - Groß Pinnow`,`Hohenselchow-Groß Pinnow - Heinrichshof`,`Hohenselchow-Groß Pinnow - Hohenselchow`,`Lychen`,`Lychen - Beenz`,`Lychen - Retzow`,`Lychen - Retzow (Kastaven)`,`Lychen - Rutenberg`,`Mescherin`,`Mescherin - Neurochlitz`,`Mescherin - Radekow`,`Mescherin - Rosow`,`Mescherin - Staffelde`,`Milmersdorf`,`Mittenwalde`,`Nordwestuckermark - Arendsee`,`Nordwestuckermark - Augustfelde`,`Nordwestuckermark - Beenz`,`Nordwestuckermark - Bülowssiege`,`Nordwestuckermark - Christianenhof`,`Nordwestuckermark - Damerow`,`Nordwestuckermark - Falkenhagen`,`Nordwestuckermark - Ferdinandshof`,`Nordwestuckermark - Ferdinandshorst`,`Nordwestuckermark - Fürstenwerder`,`Nordwestuckermark - Fürstenwerder - Fiebigershof`,`Nordwestuckermark - Gollmitz`,`Nordwestuckermark - Groß Sperrenwalde`,`Nordwestuckermark - Holzendorf`,`Nordwestuckermark - Horst`,`Nordwestuckermark - Klein Sperrenwalde`,`Nordwestuckermark - Kraatz`,`Nordwestuckermark - Kröchlendorff`,`Nordwestuckermark - Lindenhagen`,`Nordwestuckermark - Naugarten`,`Nordwestuckermark - Parmen`,`Nordwestuckermark - Raakow`,`Nordwestuckermark - Rittgarten`,`Nordwestuckermark - Röpersdorf`,`Nordwestuckermark - Schapow`,`Nordwestuckermark - Schmachtenhagen`,`Nordwestuckermark - Schönermark`,`Nordwestuckermark - Schulzenhof`,`Nordwestuckermark - Sternhagen`,`Nordwestuckermark - Warbende`,`Nordwestuckermark - Weggun`,`Nordwestuckermark - Wilhelmshayn`,`Nordwestuckermark - Wilhelmshof`,`Nordwestuckermark - Wittstock`,`Nordwestuckermark - Zernikow`,`Nordwestuckermark - Zollchow`,`Oberuckersee - Blankenburg`,`Oberuckersee - Potzlow`,`Oberuckersee - Seehausen`,`Oberuckersee - Strehlow`,`Oberuckersee - Warnitz`,`Oberuckersee - Warnitz - Grünheide`,`Oberuckersee - Warnitz - Melzow`,`Oberuckersee - Warnitz - Neuhof`,`Pinnow`,`Prenzlau`,`Prenzlau - Alexanderhof`,`Prenzlau - Basedow`,`Prenzlau - Blindow`,`Prenzlau - Dauer`,`Prenzlau - Dedelow`,`Prenzlau - Güstow`,`Prenzlau - Klinkow`,`Prenzlau - Mühlhof`,`Prenzlau - Schönwerder`,`Prenzlau - Seelübbe`,`Randowtal - Eickstedt`,`Randowtal - Schmölln`,`Randowtal - Ziemkendorf`,`Schenkenberg`,`Schönfeld`,`Schwedt-Oder`,`Schwedt-Oder - Alt-Galow`,`Schwedt-Oder - Berkholz`,`Schwedt-Oder - Blumenhagen`,`Schwedt-Oder - Briest`,`Schwedt-Oder - Criewen`,`Schwedt-Oder - Felchow`,`Schwedt-Oder - Flemsdorf`,`Schwedt-Oder - Gatow`,`Schwedt-Oder - Grünow`,`Schwedt-Oder - Heinersdorf`,`Schwedt-Oder - Hohenfelde`,`Schwedt-Oder - Jamikow`,`Schwedt-Oder - Kummerow`,`Schwedt-Oder - Kunow`,`Schwedt-Oder - Landin`,`Schwedt-Oder - Meyenburg`,`Schwedt-Oder - Neu-Galow`,`Schwedt-Oder - Passow`,`Schwedt-Oder - Schöneberg`,`Schwedt-Oder - Schönermark`,`Schwedt-Oder - Schönow`,`Schwedt-Oder - Stendell`,`Schwedt-Oder - Stützkow`,`Schwedt-Oder - Vierraden`,`Schwedt-Oder - Wendemark`,`Schwedt-Oder - Zützen`,`Tantow`,`Tantow - Damitzow`,`Tantow - Schönfeld`,`Temmen-Ringenwalde - Ringenwalde`,`Temmen-Ringenwalde - Temmen`,`Templin`,`Templin - Ahrensdorf`,`Templin - Beutel`,`Templin - Densow`,`Templin - Gandenitz`,`Templin - Gollin`,`Templin - Groß Dölln`,`Templin - Grunewald`,`Templin - Hammelspring`,`Templin - Herzfelde`,`Templin - Hindenburg`,`Templin - Klosterwalde`,`Templin - Knehden`,`Templin - Netzow`,`Templin - Petznick`,`Templin - Röddelin`,`Templin - Storkow`,`Templin - Vietmannsdorf`,`Uckerfelde - Bertikow`,`Uckerfelde - Bietikow`,`Uckerfelde - Falkenwalde`,`Uckerfelde - Hohengüstow`,`Uckerland`,`Uckerland - Lübbenow`,`Uckerland - Wolfshagen`,`Zichow`,`Zichow - Fredersdorf`,`Zichow - Golm`,|
|esn|`Neustadt`|
|mymuell|`Abens`,`Abickhafe`,`Achstetten`,`Adelschlag mit allen Ortsteilen`,`Alleshausen`,`Allmannsweiler`,`Altenbeken-Altenbeken`,`Altenbeken-Buke`,`Altenbeken-Schwaney`,`Altfunnixsiel`,`Altharlingersiel`,`Altheim`,`Altmannstein Mini Fahrzeug Altmannstein`,`Altmannstein Mini Fahrzeug für Neuenhinzenhausen, Unter der Linde und Am Bachl`,`Altmannstein Mini Fahrzeug für Sandersdorf Am Muehlberg und Wierlweg`,`Altmannstein mit Biber, Gärtnerei Wächter, Kollerhof, Landerhof, Mendorf, Pondorf, Racklhof, Steinsdorf, Stenzenhof, Viehhausen, Weiherhof`,`Altmannstein nur Althexenagger, Berghausen, Bruckhof, Dollnhof, Hagenhill, Hanfstinglmühle, Hexenagger, Hutzlmühle, Laimerstadt, Leistmühle, Neuenhinzenhausen, Neumühle, Neuses, Ottersdorf, Ried, Schafshill, Schwabstetten, Solle`,`Altmannstein nur Breitenhill, Megmannsdorf, Sandersdorf, Schamhaupten, Winden`,`Altmannstein Sondertour kleines Fahrzeug`,`Alzenau-Albstadt`,`Alzenau-Alzenau`,`Alzenau-Hörstein`,`Alzenau-Kälberau`,`Alzenau-Michelbach`,`Alzenau-Wasserlos`,`Angelsburg`,`Ardorf`,`Aschaffenburg`,`Asel`,`Attenweiler`,`Bad Arolsen`,`Bad Bentheim - 2021`,`Bad Buchau`,`Bad Driburg - 2021`,`Bad Lippspringe`,`Bad Schussenried`,`Bad Wünnenberg - Kernstadt`,`Bad Wünnenberg-Bleiwäsche`,`Bad Wünnenberg-Eilern`,`Bad Wünnenberg-Elisenhof`,`Bad Wünnenberg-Friedrichsgrund`,`Bad Wünnenberg-Fürstenberg`,`Bad Wünnenberg-Haaren`,`Bad Wünnenberg-Helmern`,`Bad Wünnenberg-Leiberg`,`Beilngries - Stadtteile Biberbach, Hirschberg, Kaldorf, Litterzhofen, Wiesenhofen, Gfösselthal, Oberndorf, Kevenhuell, Amtmannsdorf, Eglofsdorf, Kottingwförth, Leising, Paulushofen, Aschbuch, Grampersdorf, Irfersdorf, Neuzell,`,`Beilngries Mini Fahrzeug - Nur Bühlkirchenweg`,`Beilngries OT Arnbuch, Kirchbuch, Wolfsbuch`,`Beilngries Stadtgebiet`,`Bensersiel`,`Bentstreek`,`Berdum`,`Berkheim`,`Bessenbach-Keilberg`,`Bessenbach-Oberbessenbach`,`Bessenbach-Steiger`,`Bessenbach-Straßbessenbach`,`Betzenweiler`,`Beverungen`,`Biberach`,`Biberach-Mettenberg`,`Biberach-Rindenmoos`,`Biberach-Ringschnait`,`Biberach-Rißegg`,`Biberach-Stafflangen`,`Biberach-Winterreute`,`Blankenbach`,`Blaustein`,`Blersum`,`Blomberg`,`Bockhorn`,`Böhmfeld mit allen Ortsteilen`,`Borchen-Alfen`,`Borchen-Dörenhagen`,`Borchen-Etteln`,`Borchen-Kirchborchen`,`Borchen-Nordborchen`,`Borchen-Schloß Hamborn`,`Borgentreich - 2021`,`Borkum`,`Brakel - 2021`,`Bunde`,`Büren-Ahden`,`Büren-Barkhausen`,`Büren-Brenken`,`Büren-Eickhoff`,`Büren-Harth`,`Büren-Hegensdorf`,`Büren-Hegensdorf-Keddinghausen`,`Büren-Siddinghausen`,`Büren-Stadtkern`,`Büren-Steinhausen`,`Büren-Weiberg`,`Büren-Weine`,`Büren-Wewelsburg`,`Burgrieden`,`Burhafe`,`Buttforde`,`Buxheim mit allen Ortsteilen`,`Carolinensiel`,`Dammbach-Dammbach`,`Dammbach-Krausenbach`,`Dammbach-Wintersbach`,`Darmstadt`,`Delbrück - östl Kaunitz`,`Delbrück - west Kaunitz`,`Delbrück-Anreppen`,`Delbrück-Bentfeld`,`Delbrück-Boke`,`Delbrück-Hagen`,`Delbrück-Heddinghausen`,`Delbrück-Lippling`,`Delbrück-Ostenland`,`Delbrück-Schöning`,`Delbrück-Steinhorst`,`Delbrück-Westenholz`,`Denkendorf mit allen Ortsteilen`,`Dettingen`,`Dollnstein mit allen Ortsteilen`,`Dose`,`Dunum`,`Dürmentingen`,`Dürnau`,`Eberhardzell`,`Eggelingen`,`Egweil mit allen Ortsteilen`,`Eichstätt OT Buchenhuell, Landershofen, Seidlkreuz, Wasserzell, Wintershof`,`Eichstätt Stadtgebiet`,`Eitensheim mit allen Ortsteilen`,`Emlichheim - 2021`,`Erkrath`,`Erlenmoos`,`Erolzheim`,`Ertingen`,`Esens Ost`,`Esens West`,`Etzel`,`Eversmeer`,`Flensburg`,`Friedeburg`,`Friedeburg-Hesel`,`Fulkum`,`Funnix`,`Gaimersheim Hauptort`,`Gaimersheim OT Lippertshofen, Rackertshofen, Reisberg, Brunnbuck`,`Geiselbach-Geiselbach`,`Geiselbach-Omersbach`,`Glattbach`,`Goldbach-Goldbach`,`Goldbach-Unterafferbach`,`Großkrotzenburg`,`Großmehring - Hauptort mit Kleinmehring und Abdeckerei`,`Großmehring Kösching Interpark`,`Großmehring nur die Ortsteile Katharinenberg, Demling, Pettling, Theißing, Tholbath, Straßhausen, Erlachhof und Interpark komplett und Muehlen`,`Großostheim-Großostheim`,`Großostheim-Pflaumheim`,`Großostheim-Ringheim`,`Großostheim-Sonneck`,`Großostheim-Wenigumstadt`,`Gutenzell-Hürbel`,`Haan`,`Haibach-Dörrmorsbach`,`Haibach-Grünmorsbach`,`Haibach-Haibach`,`Hainburg`,`Heigenbrücken-Heigenbrücken`,`Heigenbrücken-Jakobsthal`,`Heiligenhaus`,`Heimbuchenthal`,`Heinrichsthal`,`Hepberg Mini Fahrzeug für Schloßgasse`,`Hepberg mit allen Ortsteilen`,`Hesel`,`Hilden`,`Hitzhofen mit allen Ortsteilen`,`Hochdorf`,`Hoheesche`,`Holtgast Nord`,`Holtgast Süd`,`Horsten`,`Hösbach-Bahnhof`,`Hösbach-Feldkahl`,`Hösbach-Hösbach`,`Hösbach-Rottenberg`,`Hösbach-Schmerlenbach`,`Hösbach-Wenighösbach`,`Hösbach-Winzenhohl`,`Hovel`,`Hövelhof`,`Höxter - 2021`,`Ingoldingen`,`Jemgum`,`Jever`,`Johannesberg-Breunsberg`,`Johannesberg-Johannesberg`,`Johannesberg-Oberafferbach`,`Johannesberg-Rückersbach`,`Johannesberg-Steinbach`,`Johannesberg-Sternberg`,`Jümme`,`Kahl-Heide`,`Kahl-Kahl`,`Kamp-Lintfort`,`Kanzach`,`Karlstein-Dettingen`,`Karlstein-Großwelzheim`,`Kinding mit allen Ortsteilen`,`Kipfenberg Hauptort mit den OT Buch, Groesdorf, Irlahuell, Kemathen, Oberemmendorf, Burgstraße Birktalühle`,`Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf `,`Kirchberg`,`Kirchdorf`,`Kleinkahl-Edelbach`,`Kleinkahl-Großkahl`,`Kleinkahl-Großlaudenbach`,`Kleinkahl-Kleinkahl`,`Kleinkahl-Kleinlaudenbach`,`Kleinostheim`,`Kösching Hauptort Kösching mit Desching, Badermühle, Stoll- und Blaumühle, Dürrnhof und Gradhof`,`Kösching nur die Ortsteile Kasing, Canisiushof, Gut Hellmansberg, Bettbrunn`,`Krombach`,`Langenau`,`Langenenslingen`,`Langenfeld`,`Laufach-Frohnhofen`,`Laufach-Hain`,`Laufach-Laufach`,`Laupheim`,`Laupheim-Baustetten`,`Laupheim-Bihlafingen`,`Laupheim-Obersulmetingen`,`Laupheim-Untersulmetingen`,`Leer`,`Leerhafe`,`Lenting mit allen Ortsteilen ohne Deschinger Siedlung`,`Lenting nur Deschinger Siedlung`,`Lichtenau-Asseln`,`Lichtenau-Atteln`,`Lichtenau-Blankenrode`,`Lichtenau-Dalheim`,`Lichtenau-Ebbinghausen`,`Lichtenau-Grundsteinheim`,`Lichtenau-Hakenberg`,`Lichtenau-Henglarn`,`Lichtenau-Herbram`,`Lichtenau-Herbram-Wald`,`Lichtenau-Holtheim`,`Lichtenau-Husen`,`Lichtenau-Iggenhausen`,`Lichtenau-Kleinenberg`,`Lichtenau-Lichtenau`,`Mainaschaff`,`Marienmünster - 2021`,`Marx`,`Maselheim`,`Mespelbrunn-Hessenthal`,`Mespelbrunn-Mespelbrunn`,`Mettmann`,`Mietingen`,`Mindelstetten mit allen Ortsteilen`,`Mittelbiberach`,`Mömbris-Angelsberg`,`Mömbris-Brücken`,`Mömbris-Daxberg`,`Mömbris-Dörnsteinbach`,`Mömbris-Gunzenbach`,`Mömbris-Heimbach`,`Mömbris-Hemsbach`,`Mömbris-Hohl`,`Mömbris-Kaltenberg`,`Mömbris-Königshofen`,`Mömbris-Mensengesäß`,`Mömbris-Molkenberg`,`Mömbris-Mömbris`,`Mömbris-Niedersteinbach`,`Mömbris-Rappach`,`Mömbris-Reichenbach`,`Mömbris-Rothengrund`,`Mömbris-Schimborn`,`Mömbris-Strötzbach`,`Moormerland`,`Moorweg`,`Moosburg`,`Mörnsheim mit allen Ortsteilen`,`Mühlheim`,`Mühlheim am Main`,`Musterstadt`,`Nassenfels mit allen Ortsteilen`,`Nenndorf Nord`,`Nenndorf Süd`,`Neuenhaus - 2021`,`Neuharlingersiel`,`Neuhausen`,`Neumünster`,`Neuschoo`,`Nieheim - 2021`,`Nordhorn - 2021`,`Oberdolling mit allen Ortsteilen`,`Ochsenhausen`,`Ochtersum`,`Oggelshausen`,`Ostrhauderfehn`,`Paderborn`,`Pförring mit allen Ortsteilen`,`Pollenfeld mit allen Ortsteilen`,`Ratingen`,`Reepsholt`,`Rhauderfehn`,`Riedlingen`,`Rot an der Rot`,`Rothenbuch`,`Sailauf-Eichenberg`,`Sailauf-Sailauf`,`Sailauf-Weyberhöfe`,`Salzgitter`,`Salzkotten nördlich und südlich der B1 und östlich der Heder`,`Salzkotten südlich der B1 und westlich der Heder`,`Salzkotten-Mantinghausen`,`Salzkotten-Niederntudorf`,`Salzkotten-Oberntudorf`,`Salzkotten-Scharmede`,`Salzkotten-Schwelle`,`Salzkotten-Thüle`,`Salzkotten-Upsprunge`,`Salzkotten-Verlar`,`Salzkotten-Verne`,`Sande`,`Schemmerhofen`,`Schernfeld mit allen Ortsteilen`,`Schmitten im Taunus`,`Schöllkrippen-Hofstädten`,`Schöllkrippen-Schneppenbach`,`Schöllkrippen-Schöllkrippen`,`Schöneck-Büdesheim`,`Schöneck-Kilianstädten`,`Schöneck-Oberdorfelden`,`Schortens`,`Schüttorf - 2021`,`Schweindorf`,`Schwendi`,`Seekirch`,`Seligenstadt-Froschhausen`,`Seligenstadt-Klein-Welzheim`,`Seligenstadt-Seligenstadt`,`Sommerkahl-Sommerkahl`,`Sommerkahl-Vormwald`,`Springfield`,`Stammham mit allen Ortsteilen`,`Stedesdorf`,`Steinhausen an der Rottum`,`Steinheim - 2021`,`Stockstadt am Main`,`Tannheim`,`Tiefenbach`,`Titting mit allen Ortsteilen`,`Uelsen - 2021`,`Ulm`,`Ummendorf`,`Unlingen`,`Uplengen`,`Usingen`,`Utarp`,`Uttel`,`Uttenweiler`,`Varel`,`Velbert - Kooperation beendet`,`Vöhringen`,`Volkmarsen`,`Wain`,`Waldaschaff`,`Walting mit allen Ortsteilen`,`Wangerland`,`Wangerooge`,`Warburg - 2021`,`Warthausen`,`Weener`,`Wegberg`,`Weibersbrunn-Rohrbrunn`,`Weibersbrunn-Weibersbrunn`,`Wellheim mit allen Ortsteilen`,`Werdum`,`Westerholt Nord`,`Westerholt Süd`,`Westerngrund-Huckelheim`,`Westerngrund-Oberwestern`,`Westerngrund-Unterwestern`,`Westerngrund-Westerngrund`,`Westoverledingen`,`Wettstetten mit allen Ortsteilen`,`Wiesede`,`Wiesedermeer`,`Wiesen`,`Wietmarschen - 2021`,`Wilhelmshaven`,`Willebadessen - 2021`,`Willen`,`Willmsfeld`,`Wittmund Ost`,`Wittmund Süd`,`Wittmund West`,`Wülfrath`,`xyz`,`Zetel`,`Zum Wagner`,`zz`,|

### New Version With Names

get your `service_id` from the list above.

#### For MyMuell services

Configure your `city`, `street`, `house_number` with the [https://www.mymuell.de](MyMüll.de App). The use a `city` from the list above or (if outedated) a selectable city from the app (can also be something like `Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf`) `street` and `house_number` is only needed if you get asked by the MyMüll App to provide one. If the house number is part of the street selecter it needs to be part of the street variable if the house number has its own selecter it should be in the `house_number` variable

#### for not MyMuell services

Use `city`, `street` and `house_number` argument from your providers' web page (Write them exactly like on the web page. Spelling errors may lead to errors). Note `city` argument is mandatory `street` and `house_number` are only required if your provider asks for them on their interactive web page.

### Deprecated Version With ids from terminal wizard (Still works)

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/jumomind_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/jumomind_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

import json
import re
import urllib.parse

import requests

SERVICE_MAP = [
    {
        "title": "Altenmarkt an der Triesting",
        "url": "https://www.altenmarkt-triesting.gv.at",
        "country": "at",
    },
    {"title": "Andau", "url": "https://www.andau-gemeinde.at", "country": "at"},
    {"title": "Apetlon", "url": "https://gemeinde-apetlon.at", "country": "at"},
    {"title": "Bad Blumau", "url": "https://bad-blumau-gemeinde.at", "country": "at"},
    {
        "title": "Bad Gleichenberg",
        "url": "http://www.bad-gleichenberg.gv.at",
        "country": "at",
    },
    {
        "title": "Bad Loipersdorf",
        "url": "https://gemeinde.loipersdorf.at",
        "country": "at",
    },
    {
        "title": "Bad Radkersburg",
        "url": "https://www.bad-radkersburg.gv.at",
        "country": "at",
    },
    {
        "title": "Bad Tatzmannsdorf",
        "url": "http://www.bad-tatzmannsdorf.at",
        "country": "at",
    },
    {
        "title": "Bad Waltersdorf",
        "url": "www.bad-waltersdorf.gv.at/home/",
        "country": "at",
    },
    {"title": "Bernstein", "url": "http://www.bernstein.gv.at", "country": "at"},
    {"title": "Bildein", "url": "http://www.bildein.at", "country": "at"},
    {
        "title": "Breitenbrunn am Neusiedler See",
        "url": "http://www.breitenbrunn.at",
        "country": "at",
    },
    {"title": "Breitenstein", "url": "https://www.breitenstein.at", "country": "at"},
    {"title": "Bromberg", "url": "http://www.bromberg.at", "country": "at"},
    {"title": "Bruckneudorf", "url": "http://www.bruckneudorf.eu", "country": "at"},
    {
        "title": "Buch - St. Magdalena",
        "url": "http://www.buch-stmagdalena.at",
        "country": "at",
    },
    {"title": "Burgau", "url": "https://www.burgau.info", "country": "at"},
    {
        "title": "Burgauberg-Neudauberg",
        "url": "http://www.burgauberg-neudauberg.at",
        "country": "at",
    },
    {
        "title": "Dechantskirchen",
        "url": "https://dechantskirchen.gv.at",
        "country": "at",
    },
    {
        "title": "Deutsch Goritz",
        "url": "https://www.deutsch-goritz.at",
        "country": "at",
    },
    {
        "title": "Deutsch Jahrndorf",
        "url": "https://www.deutsch-jahrndorf.at",
        "country": "at",
    },
    {
        "title": "Deutsch Kaltenbrunn",
        "url": "https://www.deutschkaltenbrunn.eu",
        "country": "at",
    },
    {"title": "Deutschkreutz", "url": "https://www.deutschkreutz.at", "country": "at"},
    {"title": "Dobl-Zwaring", "url": "https://www.dobl-zwaring.gv.at", "country": "at"},
    {"title": "Drasenhofen", "url": "https://www.drasenhofen.at", "country": "at"},
    {"title": "Draßmarkt", "url": "http://www.drassmarkt.at", "country": "at"},
    {"title": "Eberau", "url": "https://eberau.riskommunal.net", "country": "at"},
    {"title": "Eberndorf", "url": "https://www.eberndorf.at", "country": "at"},
    {"title": "Ebersdorf", "url": "https://www.ebersdorf.eu", "country": "at"},
    {"title": "Eberstein", "url": "https://www.eberstein.at", "country": "at"},
    {
        "title": "Edelsbach bei Feldbach",
        "url": "http://www.edelsbach.at",
        "country": "at",
    },
    {"title": "Eggenburg", "url": "www.eggenburg.gv.at/", "country": "at"},
    {
        "title": "Eggersdorf bei Graz",
        "url": "https://www.eggersdorf-graz.gv.at",
        "country": "at",
    },
    {"title": "Eichgraben", "url": "www.eichgraben.at/", "country": "at"},
    {"title": "Eisenstadt", "url": "https://www.eisenstadt.gv.at", "country": "at"},
    {"title": "Fehring", "url": "http://www.fehring.at", "country": "at"},
    {
        "title": "Feistritz ob Bleiburg",
        "url": "https://feistritz-bleiburg.gv.at",
        "country": "at",
    },
    {"title": "Feldbach", "url": "https://www.feldbach.gv.at", "country": "at"},
    {
        "title": "Feldkirchen in Kärnten",
        "url": "https://www.feldkirchen.at",
        "country": "at",
    },
    {"title": "Ferndorf", "url": "https://www.ferndorf.gv.at", "country": "at"},
    {
        "title": "Frankenau-Unterpullendorf",
        "url": "https://www.frankenau-unterpullendorf.gv.at",
        "country": "at",
    },
    {"title": "Frauenkirchen", "url": "https://www.frauenkirchen.at", "country": "at"},
    {"title": "Freistadt", "url": "https://www.freistadt.at", "country": "at"},
    {"title": "Fresach", "url": "https://fresach.gv.at", "country": "at"},
    {"title": "Friedberg", "url": "https://www.friedberg.gv.at", "country": "at"},
    {"title": "Frohnleiten", "url": "https://www.frohnleiten.com", "country": "at"},
    {
        "title": "Fürstenfeld",
        "url": "https://www.fuerstenfeld.gv.at",
        "country": "at",
    },
    {"title": "Gabersdorf", "url": "https://www.gabersdorf.gv.at", "country": "at"},
    {"title": "Gattendorf", "url": "https://www.gattendorf.at", "country": "at"},
    {"title": "Gitschtal", "url": "gitschtal.gv.at/", "country": "at"},
    {"title": "Gols", "url": "https://www.gols.at", "country": "at"},
    {
        "title": "Grafendorf bei Hartberg",
        "url": "https://grafendorf.at",
        "country": "at",
    },
    {
        "title": "Grafenschachen",
        "url": "https://www.grafenschachen.at",
        "country": "at",
    },
    {"title": "Grafenstein", "url": "https://grafenstein.gv.at", "country": "at"},
    {"title": "Gratkorn", "url": "https://www.gratkorn.gv.at", "country": "at"},
    {
        "title": "Gratwein-Straßengel",
        "url": "https://gratwein-strassengel.gv.at",
        "country": "at",
    },
    {
        "title": "Großsteinbach",
        "url": "www.gemeinde-grosssteinbach.at/",
        "country": "at",
    },
    {
        "title": "Großwarasdorf",
        "url": "https://www.grosswarasdorf.at",
        "country": "at",
    },
    {
        "title": "Großwilfersdorf",
        "url": "http://www.grosswilfersdorf.steiermark.at",
        "country": "at",
    },
    {
        "title": "Gutenberg",
        "url": "https://www.gutenberg-stenzengreith.gv.at",
        "country": "at",
    },
    {"title": "Güssing", "url": "https://www.guessing.co.at", "country": "at"},
    {
        "title": "Hagenberg im Mühlkreis",
        "url": "https://www.hagenberg.at",
        "country": "at",
    },
    {"title": "Hannersdorf", "url": "https://www.hannersdorf.at", "country": "at"},
    {"title": "Hartberg", "url": "https://www.hartberg.at", "country": "at"},
    {"title": "Heiligenkreuz", "url": "https://www.heiligenkreuz.at", "country": "at"},
    {
        "title": "Heiligenkreuz am Waasen",
        "url": "https://www.heiligenkreuz-waasen.gv.at",
        "country": "at",
    },
    {"title": "Heimschuh", "url": "https://www.heimschuh.at", "country": "at"},
    {"title": "Henndorf am Wallersee", "url": "www.henndorf.at/", "country": "at"},
    {"title": "Hirm", "url": "www.hirm.gv.at/", "country": "at"},
    {
        "title": "Hofstätten an der Raab",
        "url": "https://www.hofstaetten.at",
        "country": "at",
    },
    {"title": "Horitschon", "url": "http://www.horitschon.at", "country": "at"},
    {"title": "Horn", "url": "https://horn.gv.at", "country": "at"},
    {"title": "Hornstein", "url": "https://www.hornstein.at", "country": "at"},
    {"title": "Hüttenberg", "url": "https://huettenberg.at", "country": "at"},
    {"title": "Ilz", "url": "https://www.ilz.at", "country": "at"},
    {"title": "Inzenhof", "url": "https://www.inzenhof.at", "country": "at"},
    {"title": "Jabing", "url": "https://www.gemeinde-jabing.at", "country": "at"},
    {"title": "Jagerberg", "url": "http://www.jagerberg.info", "country": "at"},
    {"title": "Kaindorf", "url": "https://www.kaindorf.at", "country": "at"},
    {"title": "Kaisersdorf", "url": "http://www.kaisersdorf.com", "country": "at"},
    {
        "title": "Kalsdorf bei Graz",
        "url": "https://www.kalsdorf-graz.gv.at",
        "country": "at",
    },
    {"title": "Kapfenstein", "url": "http://www.kapfenstein.at", "country": "at"},
    {"title": "Kemeten", "url": "https://www.kemeten.gv.at", "country": "at"},
    {"title": "Kirchbach-Zerlach", "url": "www.kirchbach-zerlach.at/", "country": "at"},
    {
        "title": "Kirchberg an der Raab",
        "url": "https://www.kirchberg-raab.gv.at",
        "country": "at",
    },
    {"title": "Kittsee", "url": "https://www.kittsee.at", "country": "at"},
    {
        "title": "Kleinmürbisch",
        "url": "https://www.kleinmürbisch.at",
        "country": "at",
    },
    {"title": "Klingenbach", "url": "https://klingenbach.at", "country": "at"},
    {"title": "Klöch", "url": "https://www.kloech.com", "country": "at"},
    {"title": "Kobersdorf", "url": "www.kobersdorf.at/index.php", "country": "at"},
    {"title": "Kohfidisch", "url": "http://www.kohfidisch.at", "country": "at"},
    {"title": "Korneuburg", "url": "https://www.korneuburg.gv.at", "country": "at"},
    {"title": "Krensdorf", "url": "https://www.krensdorf.at", "country": "at"},
    {"title": "Kuchl", "url": "www.kuchl.net/", "country": "at"},
    {"title": "Laa an der Thaya", "url": "http://www.laa.at", "country": "at"},
    {
        "title": "Lackenbach",
        "url": "https://www.gemeinde-lackenbach.at",
        "country": "at",
    },
    {"title": "Lackendorf", "url": "https://www.lackendorf.at", "country": "at"},
    {"title": "Langau", "url": "http://www.langau.at", "country": "at"},
    {"title": "Langenrohr", "url": "https://www.langenrohr.gv.at", "country": "at"},
    {
        "title": "Leithaprodersdorf",
        "url": "http://www.leithaprodersdorf.at",
        "country": "at",
    },
    {
        "title": "Leutschach an der Weinstraße",
        "url": "https://www.leutschach-weinstrasse.gv.at",
        "country": "at",
    },
    {"title": "Lieboch", "url": "https://www.lieboch.gv.at", "country": "at"},
    {"title": "Litzelsdorf", "url": "https://www.litzelsdorf.at", "country": "at"},
    {"title": "Lockenhaus", "url": "www.lockenhaus.at/", "country": "at"},
    {
        "title": "Loipersbach im Burgenland",
        "url": "https://www.loipersbach.info",
        "country": "at",
    },
    {"title": "Mariasdorf", "url": "https://www.mariasdorf.at", "country": "at"},
    {
        "title": "Markt Hartmannsdorf",
        "url": "https://www.markthartmannsdorf.at",
        "country": "at",
    },
    {"title": "Markt Neuhodis", "url": "http://www.markt-neuhodis.at", "country": "at"},
    {"title": "Marz", "url": "https://www.marz.gv.at", "country": "at"},
    {"title": "Mattersburg", "url": "https://www.mattersburg.gv.at", "country": "at"},
    {"title": "Meiseldorf", "url": "https://www.meiseldorf.gv.at", "country": "at"},
    {"title": "Melk", "url": "https://www.stadt-melk.at", "country": "at"},
    {
        "title": "Mettersdorf am Saßbach",
        "url": "http://www.mettersdorf.com",
        "country": "at",
    },
    {"title": "Miesenbach", "url": "https://www.miesenbach.at", "country": "at"},
    {"title": "Mischendorf", "url": "https://www.mischendorf.at", "country": "at"},
    {"title": "Mistelbach", "url": "https://www.mistelbach.at", "country": "at"},
    {
        "title": "Mitterdorf an der Raab",
        "url": "https://www.mitterdorf-raab.at",
        "country": "at",
    },
    {"title": "Mureck", "url": "https://www.mureck.gv.at", "country": "at"},
    {"title": "Mönchhof", "url": "https://www.moenchhof.at", "country": "at"},
    {
        "title": "Mörbisch am See",
        "url": "https://moerbisch.gv.at",
        "country": "at",
    },
    {
        "title": "Neudorf bei Parndorf",
        "url": "http://www.neudorfbeiparndorf.at",
        "country": "at",
    },
    {"title": "Neudörfl", "url": "https://www.neudoerfl.gv.at", "country": "at"},
    {
        "title": "Neufeld an der Leitha",
        "url": "https://www.neufeld-leitha.at",
        "country": "at",
    },
    {
        "title": "Neusiedl am See",
        "url": "https://www.neusiedlamsee.at",
        "country": "at",
    },
    {
        "title": "Neustift bei Güssing",
        "url": "http://www.xn--neustift-bei-gssing-jbc.at",
        "country": "at",
    },
    {"title": "Nickelsdorf", "url": "https://www.nickelsdorf.gv.at", "country": "at"},
    {
        "title": "Oberpullendorf",
        "url": "https://www.oberpullendorf.gv.at",
        "country": "at",
    },
    {
        "title": "Oberschützen",
        "url": "https://www.oberschuetzen.at",
        "country": "at",
    },
    {"title": "Oberwart", "url": "https://www.oberwart.gv.at", "country": "at"},
    {"title": "Oslip", "url": "http://www.oslip.at", "country": "at"},
    {
        "title": "Ottendorf an der Rittschein",
        "url": "https://www.ottendorf-rittschein.steiermark.at",
        "country": "at",
    },
    {"title": "Paldau", "url": "http://www.paldau.gv.at", "country": "at"},
    {"title": "Pama", "url": "https://www.gemeinde-pama.at", "country": "at"},
    {"title": "Pamhagen", "url": "https://www.gemeinde-pamhagen.at", "country": "at"},
    {"title": "Parndorf", "url": "http://www.gemeinde-parndorf.at", "country": "at"},
    {"title": "Payerbach", "url": "https://www.payerbach.at", "country": "at"},
    {"title": "Peggau", "url": "https://peggau.at", "country": "at"},
    {"title": "Pernegg an der Mur", "url": "http://pernegg.at", "country": "at"},
    {
        "title": "Pernegg im Waldviertel",
        "url": "https://www.pernegg.info",
        "country": "at",
    },
    {
        "title": "Pfarrwerfen",
        "url": "http://www.gemeinde.pfarrwerfen.at",
        "country": "at",
    },
    {"title": "Pilgersdorf", "url": "https://www.pilgersdorf.at", "country": "at"},
    {"title": "Pinggau", "url": "https://www.pinggau.gv.at", "country": "at"},
    {"title": "Pinkafeld", "url": "https://www.pinkafeld.gv.at", "country": "at"},
    {
        "title": "Podersdorf am See",
        "url": "http://www.gemeindepodersdorfamsee.at",
        "country": "at",
    },
    {"title": "Poggersdorf", "url": "https://gemeinde-poggersdorf.at", "country": "at"},
    {"title": "Potzneusiedl", "url": "https://www.potzneusiedl.at", "country": "at"},
    {"title": "Poysdorf", "url": "https://www.poysdorf.at", "country": "at"},
    {"title": "Pöchlarn", "url": "https://www.poechlarn.at", "country": "at"},
    {"title": "Raach am Hochgebirge", "url": "https://www.raach.at", "country": "at"},
    {"title": "Raasdorf", "url": "www.raasdorf.gv.at/", "country": "at"},
    {"title": "Radmer", "url": "https://www.radmer.at", "country": "at"},
    {"title": "Ragnitz", "url": "https://www.ragnitz.gv.at", "country": "at"},
    {"title": "Raiding", "url": "https://www.raiding-online.at", "country": "at"},
    {"title": "Reichenau", "url": "https://reichenau.gv.at", "country": "at"},
    {
        "title": "Rohr bei Hartberg",
        "url": "https://www.rohr-bei-hartberg.at",
        "country": "at",
    },
    {"title": "Rohr im Burgenland", "url": "www.rohr-bgld.at/", "country": "at"},
    {"title": "Rudersdorf", "url": "http://www.rudersdorf.at", "country": "at"},
    {"title": "Rust", "url": "https://www.freistadt-rust.at", "country": "at"},
    {
        "title": "Saalfelden am Steinernen Meer",
        "url": "www.stadtmarketing-saalfelden.at/de",
        "country": "at",
    },
    {
        "title": "Sankt Georgen an der Stiefing",
        "url": "https://www.st-georgen-stiefing.gv.at",
        "country": "at",
    },
    {"title": "Sankt Gilgen", "url": "https://www.gemgilgen.at", "country": "at"},
    {
        "title": "Sankt Oswald bei Plankenwarth",
        "url": "https://www.sanktoswald.net",
        "country": "at",
    },
    {
        "title": "Schrattenberg",
        "url": "https://www.schrattenberg.gv.at",
        "country": "at",
    },
    {"title": "Schwadorf", "url": "https://www.schwadorf.gv.at", "country": "at"},
    {"title": "Schäffern", "url": "https://www.schaeffern.gv.at", "country": "at"},
    {
        "title": "Schützen am Gebirge",
        "url": "https://www.schuetzen-am-gebirge.at",
        "country": "at",
    },
    {
        "title": "Seiersberg-Pirka",
        "url": "https://www.gemeindekurier.at",
        "country": "at",
    },
    {"title": "Siegendorf", "url": "https://www.siegendorf.gv.at", "country": "at"},
    {"title": "Sigleß", "url": "https://www.sigless.at", "country": "at"},
    {
        "title": "Sigmundsherberg",
        "url": "https://www.sigmundsherberg.gv.at",
        "country": "at",
    },
    {
        "title": "Sinabelkirchen",
        "url": "https://www.sinabelkirchen.eu",
        "country": "at",
    },
    {"title": "St. Andrä", "url": "https://www.st-andrae.gv.at", "country": "at"},
    {
        "title": "St. Andrä am Zicksee",
        "url": "https://www.gemeinde-standrae.at",
        "country": "at",
    },
    {
        "title": "St. Anna am Aigen",
        "url": "http://www.st-anna-aigen.gv.at",
        "country": "at",
    },
    {
        "title": "St. Egyden am Steinfeld",
        "url": "https://www.st-egyden.at",
        "country": "at",
    },
    {
        "title": "St. Georgen an der Leys",
        "url": "www.stgeorgenleys.at/",
        "country": "at",
    },
    {
        "title": "St. Jakob im Rosental",
        "url": "www.st-jakob-rosental.gv.at/",
        "country": "at",
    },
    {
        "title": "St. Johann in der Haide",
        "url": "http://www.st-johann-haide.gv.at",
        "country": "at",
    },
    {"title": "St. Konrad", "url": "www.st-konrad.at/", "country": "at"},
    {
        "title": "St. Lorenzen am Wechsel",
        "url": "https://www.st-lorenzen-wechsel.at",
        "country": "at",
    },
    {
        "title": "St. Margarethen an der Raab",
        "url": "https://www.st-margarethen-raab.at",
        "country": "at",
    },
    {
        "title": "St. Margarethen im Burgenland",
        "url": "https://www.st-margarethen.at",
        "country": "at",
    },
    {
        "title": "St. Peter - Freienstein",
        "url": "https://www.st-peter-freienstein.gv.at",
        "country": "at",
    },
    {
        "title": "St. Peter am Ottersbach",
        "url": "http://www.st-peter-ottersbach.gv.at",
        "country": "at",
    },
    {
        "title": "St. Ruprecht an der Raab",
        "url": "https://www.st.ruprecht.at",
        "country": "at",
    },
    {
        "title": "St. Veit in der Südsteiermark",
        "url": "https://www.st-veit-suedsteiermark.gv.at",
        "country": "at",
    },
    {"title": "Stegersbach", "url": "https://gemeinde.stegersbach.at", "country": "at"},
    {"title": "Steinbrunn", "url": "https://www.steinbrunn.at", "country": "at"},
    {"title": "Steuerberg", "url": "https://www.steuerberg.at", "country": "at"},
    {"title": "Stinatz", "url": "http://www.stinatz.gv.at", "country": "at"},
    {"title": "Stiwoll", "url": "https://www.stiwoll.at", "country": "at"},
    {"title": "Stockerau", "url": "http://www.stockerau.at", "country": "at"},
    {
        "title": "Straß in Steiermark",
        "url": "https://www.strass-steiermark.gv.at",
        "country": "at",
    },
    {
        "title": "Söchau",
        "url": "http://www.soechau.steiermark.at",
        "country": "at",
    },
    {"title": "Tadten", "url": "https://www.tadten.at", "country": "at"},
    {"title": "Tattendorf", "url": "https://www.tattendorf.at", "country": "at"},
    {"title": "Thal", "url": "https://thal.gv.at", "country": "at"},
    {"title": "Tieschen", "url": "https://www.tieschen.gv.at", "country": "at"},
    {"title": "Tobaj", "url": "http://www.tobaj.gv.at", "country": "at"},
    {"title": "Tulln an der Donau", "url": "https://www.tulln.at", "country": "at"},
    {
        "title": "Unterfrauenhaid",
        "url": "https://www.unterfrauenhaid.at",
        "country": "at",
    },
    {
        "title": "Unterkohlstätten",
        "url": "https://www.unterkohlstaetten.at",
        "country": "at",
    },
    {"title": "Unterlamm", "url": "http://www.unterlamm.gv.at", "country": "at"},
    {"title": "Unterwart", "url": "https://www.unterwart.at", "country": "at"},
    {"title": "Vasoldsberg", "url": "https://www.vasoldsberg.gv.at", "country": "at"},
    {
        "title": "Vordernberg",
        "url": "http://www.vordernberg.steiermark.at",
        "country": "at",
    },
    {"title": "Völkermarkt", "url": "https://voelkermarkt.gv.at", "country": "at"},
    {"title": "Walpersbach", "url": "http://www.walpersbach.gv.at", "country": "at"},
    {"title": "Weiden am See", "url": "https://www.weiden-see.at", "country": "at"},
    {"title": "Weitersfeld", "url": "https://www.weitersfeld.gv.at", "country": "at"},
    {"title": "Weiz", "url": "https://www.weiz.at", "country": "at"},
    {"title": "Weppersdorf", "url": "https://www.weppersdorf.at", "country": "at"},
    {
        "title": "Werfenweng",
        "url": "http://www.gemeinde-werfenweng.at",
        "country": "at",
    },
    {"title": "Wies", "url": "https://www.wies.at", "country": "at"},
    {"title": "Wiesen", "url": "https://www.wiesen.eu", "country": "at"},
    {"title": "Wiesfleck", "url": "https://www.gemeinde-wiesfleck.at", "country": "at"},
    {"title": "Wiesmath", "url": "http://www.wiesmath.at", "country": "at"},
    {
        "title": "Wimpassing an der Leitha",
        "url": "http://www.wimpassing-leitha.at",
        "country": "at",
    },
    {"title": "Winden am See", "url": "https://www.winden.at", "country": "at"},
    {"title": "Wolfau", "url": "https://www.gemeinde-wolfau.at", "country": "at"},
    {"title": "Wolfsberg", "url": "https://www.wolfsberg.at", "country": "at"},
    {
        "title": "Wolkersdorf im Weinviertel",
        "url": "http://www.wolkersdorf.at",
        "country": "at",
    },
    {
        "title": "Wulkaprodersdorf",
        "url": "https://www.wulkaprodersdorf.at",
        "country": "at",
    },
    {"title": "Wörterberg", "url": "http://www.woerterberg.at", "country": "at"},
    {"title": "Zagersdorf", "url": "http://www.zagersdorf.at", "country": "at"},
    {
        "title": "Zelking-Matzleinsdorf",
        "url": "http://www.zelking-matzleinsdorf.gv.at",
        "country": "at",
    },
    {"title": "Zillingtal", "url": "https://www.zillingtal.eu", "country": "at"},
    {"title": "Zurndorf", "url": "https://zurndorf.at", "country": "at"},
    {"title": "Übelbach", "url": "https://www.uebelbach.gv.at", "country": "at"},
]


class CitiesApps:
    def __init__(self, password, email=None, phone=None) -> None:
        if (email is None and phone is None) or password is None:
            raise Exception("(email or phone) and password required")
        if email is not None and phone is not None:
            raise Exception("Only provide one of email or phone not both")

        # get authentication as guest
        self._session = requests.Session()
        self._session.headers.update(
            {
                "user-agent": "cities/100.100.100/Android",
                "requesting-app": "user-android",
            }
        )

        username = phone if email is None else email
        r = self._session.post(
            "https://api.v2.citiesapps.com/auth",
            json={
                "method": "email" if email is not None else "phoneNumber",
                "emailOrPhoneNumber": username,
                "password": password,
            },
        )
        if r.status_code == 400:
            raise Exception("failed to login to the App, check your login credentials")
        r.raise_for_status()

        self._session.headers.update({"authorization": r.headers["access-token"]})

    def get_cities(self) -> list:
        cities = []
        next_url = "/cities?pagination=limit:100"
        while next_url:
            r = self._session.get("https://api.v2.citiesapps.com" + next_url)
            r.raise_for_status()
            j = r.json()
            next_url = j["nextUrl"]
            cities += j["data"]
        return cities

    def get_specific_citiy(self, search: str) -> dict | None:
        for city in self.get_cities():
            if city["name"].lower().strip() == search.lower().strip():
                return city
        return None

    def get_garbage_calendars(self, city_id: str) -> list:
        params = {
            "filter": json.dumps(
                {"entityid": {"$in": [city_id]}}, separators=(",", ":")
            ),
        }
        params_str = urllib.parse.urlencode(params, safe=":$")

        r = self._session.get(
            "https://api.citiesapps.com/garbagecalendars/filter", params=params_str
        )
        r.raise_for_status()
        return r.json()["garbage_calendars"]

    def get_streets(self, city_id):
        params = {
            "entityid": [city_id],
        }

        r = self._session.get("https://api.citiesapps.com/garbageareas", params=params)
        r.raise_for_status()
        return r.json()

    def get_specific_calendar(self, city_id: str, search: str) -> dict | None:
        for calendar in self.get_garbage_calendars(city_id):
            if calendar["name"].lower().strip() == search.lower().strip():
                return calendar
        return None

    def get_garbage_plans(self, garbage_calendar: dict) -> list:
        r = self._session.get(
            "https://api.citiesapps.com/garbagecalendars/",
            params={"full": "true", "ids": garbage_calendar["_id"]},
        )
        r.raise_for_status()
        garbage_plans = []
        for cal in r.json():
            garbage_plans += cal["garbage_plans"]
        return garbage_plans

    def fetch_garbage_plans(self, city: str, calendar: str):
        city_dict = self.get_specific_citiy(city)
        if not city_dict:
            raise Exception("City not found")
        city_id = city_dict["_id"]

        specific_calendar = self.get_specific_calendar(city_id, calendar)
        if not specific_calendar:
            raise Exception("Calendar not found")

        return self.get_garbage_plans(specific_calendar)

    def get_supported_cities(self) -> dict[str, list]:
        supported_dict: dict[str, list] = {"supported": [], "not_supported": []}
        for city in self.get_cities():
            if self.get_garbage_calendars(city["_id"]):
                supported_dict["supported"].append(city)
            else:
                supported_dict["not_supported"].append(city)
        return supported_dict

    def get_city_home_page(self, city):
        city_page_id = city["cityPage"]["_id"]
        r = self._session.get(
            f"https://api.v2.citiesapps.com/pages/{city_page_id}?include=tabBar"
        )
        r.raise_for_status()
        j = r.json()
        if "website" not in j:
            if city["name"] in SERVICE_MAP:
                return SERVICE_MAP[city["name"]]
            return ""
        return j["website"]

    def generate_service_map(self) -> list[dict[str, str]]:
        supported_dict = self.get_supported_cities()
        if len(supported_dict["not_supported"]) > 0:
            print(
                "# not supported: ",
                len(supported_dict["not_supported"]),
                ":",
                supported_dict["not_supported"],
            )
        service_map = []

        supported_len = len(supported_dict["supported"])
        for id, city in enumerate(supported_dict["supported"]):
            if city["name"] in [c["title"] for c in SERVICE_MAP]:
                city_homepage = [
                    c["url"] for c in SERVICE_MAP if city["name"] == c["title"]
                ][0]
            else:
                print(f"{id+1}/{supported_len} {city['name']}")
                city_homepage = self.get_city_home_page(city)

            slash_index = [m.start() for m in re.finditer("/", city_homepage)]
            domain_end = slash_index[2] if len(slash_index) > 2 else len(city_homepage)
            url = city_homepage[:domain_end]
            # city["country_abbreviation"] returns "de" instead of "at" sometimes
            service_map.append({"title": city["name"], "url": url, "country": "at"})
        return service_map


if __name__ == "__main__":
    c = CitiesApps(email=input("email: "), password=input("password: "))
    service_map = c.generate_service_map()
    service_map_copy = SERVICE_MAP.copy()

    print("[")
    for service in service_map:
        print(4 * " " + "{")
        for key, value in service.items():
            print(8 * " " + f'"{key}": "{value}",')
        print(4 * " " + "},")
    print("]")

    print("\nchanges to the service map:")
    for new_service in service_map:
        found = False
        for service in SERVICE_MAP:
            if new_service["title"] == service["title"]:
                if service["url"] != new_service["url"]:
                    print(
                        f"{new_service['title']}: {service['url']} -> {new_service['url']}"
                    )
                found = True
                service_map_copy.remove(service)
                break
        if not found:
            print(f"new service: {new_service['title']}: {new_service['url']}")
    for service in service_map_copy:
        print(f"service removed: {service['title']}: {service['url']}")

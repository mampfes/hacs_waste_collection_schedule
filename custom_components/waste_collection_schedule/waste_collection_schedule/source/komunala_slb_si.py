import base64
import urllib.parse
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import ICSTransformer

MAIN_REGIONS = {
    (
        "1: DEŽNO PRI MAKOLAH, GLOBOKO OB DRAVINJI, JELOVEC PRI MAKOLAH, MAKOLE, "
        "MOSTEČNO, PEČKE, SAVINSKO, SESTRŽE, STARI GRAD, STOPNO, STRANSKE MAKOLE, "
        "STRUG, ŠTATENBERG, VAROŠ"
    ): "aDBlNWNoZ20zMGx1NnJzYTloMW40OHNiZnNAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "2: BEZINA, BOŽJE, BREZJE PRI OPLOTNICI, GORICA PRI OPLOTNICI, KORITNO, "
        "KOVAŠKI VRH, LAČNA GORA, MALAHORNA, OPLOTNICA: Cesta na polje, Fošt, "
        "Goriška cesta, Grajska cesta, Granitna ulica, Konjiška cesta, "
        "Prešernova cesta, Strma ulica, Travniška cesta"
    ): "bXNtaXBxNmJ1ODFxMHJrYTAyNmhla29qYmdAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "3: ČADRAM, DOBRIŠKA VAS, DOBROVA PRI PRIHOVI, MARKEČICA, OPLOTNICA: Gmajna, "  # codespell:ignore vas
        "Partizanska cesta, Pohorska cesta, Prečna ulica, Šolska ulica, "
        "Ulica 22. maja, Ulica Pohorskega Bataljona, Vinogradna cesta, Vrtna ulica, "
        "POBREŽ, RASKOVEC, STRAŽA PRI OPLOTNICI, UGOVEC (h. št. 1, 1a, 29, 30, 32, 33, 34, 35)"
    ): "cG5mcms2MWhiMGNhbG9ia3Y4aGptaGw2amNAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "4: GLADOMES (h. št. 35, 35a, 35b, 37, 37a, 37b, 39, 40, 40a, 41, 41a, 41b, "
        "42, 43, 44, 44a, 45, 46, 46a, 46b, 46c, 47, 47a, 48, 49, 50, 51), KORPLJE, "
        "OKOŠKA GORA, PRELOGE, PREPUŽ, PRIHOVA, SEVEC, SPODNJA LOŽNICA (h. št. 10, 10a), "
        "UGOVEC (h. št. od 2 do 28), VINARJE, VRHOLE PRI SLOVENSKIH KONJICAH, "
        "ZGORNJA LOŽNICA (h. št. 64, 65, 65a, 66, 66a, 66b, 67, 68a, 69), "
        "ZGORNJE GRUŠOVJE, ZLOGONA GORA, ZLOGONA VAS"  # codespell:ignore vas
    ): "ZjhhZzhvZmtibjhkbzltODhkM25hMTVocjhAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "5: BREZJE PRI POLJČANAH, BREZJE PRI SLOVENSKI BISTRICI, ČREŠNJEVEC (h. št. 144b), "
        "DRUMLAŽNO, FAROVEC, HRASTOVEC POD BOČEM, JEŠOVEC, KOČNO OB LOŽNICI, KRASNA, "
        "KRIŽEČA VAS, LOŽNICA, MODRAŽE, NOVAKE, PRETREŽ, STUDENICE, "  # codespell:ignore vas
        "TRNOVEC PRI SLOVENSKI BISTRICI, VRHLOGA, VRHOLE PRI LAPORJU (razen h. št. 31)"
    ): "ODdqbmRvdGxkcm82YjZ1a2ttYXI3dnBmZGtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "6: ČREŠNJEVEC (h. št. 129, 130, 131, 131a), FOŠT, GLADOMES (h. št. od 1 do 33, "
        "od 53 do 93), KOSTANJEVEC, LESKOVEC, SPODNJA LOŽNICA, STARI LOG (h. št. 69, 72), "
        "TINJSKA GORA, VISOLE (h. št. 154, 154a, 154b, 154c, 156, 157, 158, od 160 do 177), "
        "ZGORNJA BISTRICA (h. št. 35, 37, 39, 41, od 43 do 46), "
        "ZGORNJA LOŽNICA (h. št. od 1 do 63, 69a, od 70 do 88)"
    ): "MjFjODkyOW5vaTB2MTI5M2k5dXE5MjduN2tAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "7: GABERNIK (h. št. 89, 90, 94), KALŠE, KLOPCE, KOČNO PRI POLSKAVI, "
        "NOVA GORA NAD SLOVENSKO BISTRICO, OGLJENŠAK (h. št. 10, 10a, 16, 16a, 16b, "
        "16c, 17, 18, 18a, 18b, 19, 19a, 19B, 19c, 20, 20a, 21, 44, 45, 46, 47, 48, "
        "49, 50, 51, 52, 53), OŠELJ, PLANINA POD ŠUMIKOM (h. št. 7), POKOŠE (razen h. št. 42), "
        "RITOZNOJ (razen h. št. 2), SLOVENSKA BISTRICA: Devinska ulica, SMREČNO, "
        "SPODNJE PREBUKOVJE, ŠENTOVEC, ŠMARTNO NA POHORJU, ZGORNJA NOVA VAS, "  # codespell:ignore vas
        "ZGORNJA POLSKAVA: Partizanska ulica (h. št. 31), ZGORNJE PREBUKOVJE"
    ): "bDM3ZzMya2dvMTJ0djc4YWRtY3JoaXR1M29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "8: BUKOVEC, GABERNIK (razen h. št. 89, 90, 94), LOKA PRI FRAMU (h. št. 14, 14a), "
        "OGLJENŠAK (h. št. od 3 do 9a, od 11 do 15, od 22 do 43), RITOZNOJ (h. št. 2), "
        "ZGORNJA POLSKAVA"
    ): "amVzZmk0cTFlOW8zaWc3ZThrNTZjcmg0NW9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "9: HOŠNICA, POLJČANE: Bevkova ulica, Bistriška cesta, Čretniška ulica, "
        "Dravinjska cesta, Gregorčičeva ulica, Kajuhova ulica, Laporska cesta, "
        "Ob železnici, Strma ulica, Tovarniška ulica, Vrtna ulica, "
        "Ulica Bračičeve brigade, Ulica Šercerjeve brigade, SPODNJA BREŽNICA, "
        "SPODNJE POLJČANE: Dravinjska cesta, Ježev dol, Nova ulica, Ob potoku, "
        "Prečna ulica, Seliškarjeva ulica, Ulica 9. maja, Ulica Prekomorske brigade, "
        "Ulica Šlandrove brigade, Ulica Tomšičeve brigade, Vorančeva ulica, "
        "VRHOLE PRI LAPORJU (h. št. 31), ZGORNJA BREŽNICA"
    ): "MHU1NjIwcDJwYzE0ZGVtb3JwOHByODBlb2tAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "10: ČADRAMSKA VAS, DOLGI VRH, LEVIČ, LJUBIČNO (h. št. 38, 40), LOVNIK, "  # codespell:ignore vas
        "LUŠEČKA VAS, PODBOČ, POLJČANE: Na hribu, RAZGOR PRI ŽABLJEKU, STANOVSKO, "  # codespell:ignore vas
        "ZGORNJE POLJČANE: Kopališka ulica, Maistrova ulica, Na Boč, Ob Beli (razen h. št. 7), "
        "Partizanska ulica, Potrčeva ulica, Prvomajski trg, Rimska ulica, Rogaška cesta, "
        "Ulica Erne Starovasnik, ŽABLJEK"
    ): "cDU2OGFyM3NtNjgzMzdraDZmNHY2NDlodTBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "11: CEZLAK, JURIŠNA VAS, KEBELJ, KOT NA POHORJU, LUKANJA, MALO TINJE, "  # codespell:ignore vas
        "MODRIČ, NADGRAD, PLANINA POD ŠUMIKOM (h. št. 16b, 20, 21), PODGRAD NA POHORJU, "
        "RADKOVEC, REP (razen h. št. 8, 9), SLOVENSKA BISTRICA: Aljaževa ulica, "
        "Ljubljanska cesta (h. št. od 90 do 127), Pirnikova ulica, Stepišnikova (h. št.: 8, 8A), "
        "V Zafošt, Vodovnikova ulica, SPODNJA LOŽNICA (h. št. 40, 42, 42A, 43, 43a, 55), "
        "TURIŠKA VAS NA POHORJU, URH, VELIKO TINJE, VISOLE (razen h. št. 154, 154a, 154b, "  # codespell:ignore vas
        "154c, 156, 157, 158, od 160 do 176), ZGORNJA BISTRICA (h. št. od 1 do 6, od 8 do 10, "
        "od 12 do 34, 36, 38, 40, 47, 50, 52)"
    ): "MmNkaTJ2bXE3a3FkZWtub2dubXQ5MGVuNG9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "12: DEVINA, KOVAČA VAS, SLOVENSKA BISTRICA: Gombačeva ulica, Grajska ulica, "  # codespell:ignore vas
        "Grogova ulica, Kratka ulica, Mariborska cesta, Mladinska ulica, Na Jožefu, "
        "Ob parku, Štuhčeva ulica, Trg Alfonza Šarha, Ulica dr. Štefke Hribar, "
        "Ulica Pohorskega Bataljona, Ulica Sagadinovih, Zidanškova ulica, "
        "ZGORNJA BISTRICA (h. št. od 60 do 168)"
    ): "ZWF1c25zampkdHNiNGJ0cWEyYjNtbWIzMmtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "13: CIGONCA, KRIŽNI VRH, LAPORJE, LOKANJA VAS, SLOVENSKA BISTRICA: "  # codespell:ignore vas
        "Bazoviška ulica, Stepišnikova ulica (razen h. št. 8, 8a), SPODNJA LOŽNICA "
        "(h. št. 8, 9), SPODNJA NOVA VAS (razen h. št. 1a, 45, 47, 47a, 48), VIDEŽ"  # codespell:ignore vas
    ): "dmdxaXVnMjVqMjE0Y29rNnQ0dDM0MGE4cDhAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "14: ČREŠNJEVEC (razen h. št. 129, 130, 131, 131a, 144b), SELE PRI POLSKAVI, "
        "SPODNJA POLSKAVA, STARI LOG"
    ): "ZjJnanM1dDU5YmlkNTBpNWFrYXBzZ2Jtcm9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "15: GAJ, PRAGERSKO, SLOVENSKA BISTRICA: Izseljenska ulica, Jurčičeva ulica, "
        "Leskovarjeva ulica, Miklošičeva ulica, Prečna ulica, Romihova ulica, "
        "Slovenska ulica, Tavčarjeva ulica, Ulica Borisa Winterja, Ulica dr. Jagodiča, "
        "Vošnjakova ulica, Zelena ulica, SPODNJA GORICA, SPODNJI GAJ PRI PRAGERSKEM, "
        "ZGORNJA GORICA"
    ): "ZTdjdWNxaWhhanI5MzVxcDRjamVmcXI1azRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "16: BREZULA, PODOVA, RAČE: Cesta talcev, Drevesniška ulica, Gasilska ulica, "
        "Gortanova ulica, Grajski trg, Kolodvorska ulica, Križna pot, Ljubljanska cesta, "
        "Lončarska ulica, Mariborska cesta, Mladinska ulica, Nova ulica, Ob potoku, "
        "Obrtniška ulica, Opekarniška ulica, Ozka ulica, Poljska cesta, Pot k mlinu, "
        "Pot na Gomilo, Pred njivami, Pri kozolcih, Ptujska cesta, Sadjarska ulica, "
        "Sončna ulica, Ulica Ivana Šalamuna, Ulica Lackove čete, Vrtna ulica, Za vrtovi"
    ): "dmE5cDd1MGhyZmhqZ2owYjVycHJtY3EwcmtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "17: FRAM: Bistriška cesta, Cesta na Bukovec, Cesta na Ješenco, Dobrava, "  # codespell:ignore fram
        "Eberlova ulica, Framska ulica, K ribniku, Kopivniška cesta, Koropčeva ulica, "
        "Kratka ulica, Mlinska ulica, Ob sadovnjaku, Pirkmajerjeva ulica, Sončna ulica, "
        "Turnerjeva ulica (h. št. od 58 do 108), Ulica talcev, V gaj, Varta, Za vrtcem, "
        "JEŠENCA (h. št. od 11 do 79), KOPIVNIK (h. št. 1, 12a, 12b), "
        "LOKA PRI FRAMU (h. št. od 1 do 10), MORJE: Bistriška cesta, Brezovec, "
        "Cesta na Bukovec, Cestarska pot, Cvetlična ulica, Čebelarska ulica, "
        "Koropčeva ulica, Log, Med vinogradi, Mlinska ulica, Morska cesta, Na livadi, "
        "Ob gozdu, Ob potoku, Pod terasami, Priolova cesta, Prisojna ulica, Ravna ulica, "
        "Senčna ulica, Sončne terase, Stara gora, Strma ulica, Tajna, Zavita ulica, "
        "Zelena ulica, POŽEG"
    ): "aWg2bjQ5amliZXA4cWo0c3FycHQ1ZzFqZW9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "18: FRAM: Cafova ulica, Cesta v Ranče, Črešnjev vrh, Na hribu, Nad gradom, "  # codespell:ignore fram
        "Oljarska ulica, Pohorska cesta, Turnerjeva ulica (h. št. od 1 do 57 in od 109 do 127), "
        "JEŠENCA (h. št. od 1 do 10), KOPIVNIK (razen h. št. 1, 12a, 12b), "
        "LOKA PRI FRAMU (h. št. od 10 do 37), PLANICA, RAČE: Delavska ulica, "
        "Glaserjeva ulica, Gozdna ulica, Mejna ulica, Ob železnici, Prečna ulica, "
        "Turnerjeva ulica, Ulica bratov Turjakov, RANČE, ŠESTDOBE"
    ): "NDR0Ym9mYzJxamprNXQ4NGNyZXNwdTJiaGdAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "19: SLOVENSKA BISTRICA: Čopova ulica, Gradišče, Jamova ulica, Kolodvorska ulica, "
        "Kopališka ulica, Kraigherjeva ulica, Levstikova ulica, Mroževa ulica, "
        "Na Ajdov hrib, Ob gozdu, Ob potoku, Ob stadionu, Osojna ulica, Ozka ulica, "
        "Partizanska cesta, Prežihova ulica, Prvomajska ulica, Ratejeva ulica, "
        "Ribiška ulica, Samova ulica, Sernčeva ulica, Slomškova ulica, Šolska ulica, "
        "Tomšičeva ulica, Tovarniška ulica, Travniška ulica, Trg svobode, "
        "Ulica Bračičeve Brigade, Ulica dr. Jožeta Pučnika, Ulica Pohorskega Odreda, "
        "Vinarska ulica, Zadružna ulica"
    ): "ZmgyZzE4MWVhaWlib2s2NW1mc2E0Zm45YzBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "20: POKOŠE (h. št. 42), SLOVENSKA BISTRICA: Aškerčeva ulica, Cankarjeva ulica, "
        "Cesta zmage, Cesta XIV divizije, Cvetlična ulica, Finžgarjeva ulica, "
        "Gregorčičeva ulica, Industrijska ulica, Ingoličeva ulica, Jenkova ulica, "
        "Kajuhova ulica, Kettejeva ulica, Krekova ulica, Lackova ulica, Leonova ulica, "
        "Livadna, Ljubljanska cesta (h. št. od 1 do 89), Maistrova ulica, Murnova ulica, "
        "Na poljanah, Obrtniška ulica, Plečnikova ulica, Potrčeva ulica, Prešernova ulica, "
        "Proti Jezam, Rimska ulica, Špindlerjeva ulica, Štancerjeva ulica, Tomažičeva ulica, "
        "Trgovska ulica, Trubarjeva ulica, Ulica Anice Černejeve, Ulica Slave Klavore, "
        "V Črnec (h. št. 1, 3, 4, 5, 7), Vrtnarska ulica, Žolgarjeva ulica, Župančičeva ulica, "
        "SPODNJA NOVA VAS (h. št. 45, 47, 47a, 48), ZGORNJA BISTRICA (h. št. 7, 11)"  # codespell:ignore vas
    ): "cnZpOGp1NzdtOW1qbDZqbGgwbjluN29kbDBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "21: BOŽJE (h. št. 1, 1a, 3, 4, 5), CEZLAK (h. št. 20, 21, 23), "
        "ČADRAM (h. št. 36, 36a, 37, 38a, 39a, 40, 41), GORICA PRI OPLOTNICI (h. št. 1, 2, 3, 5, 6, 9, 12), "
        "KORITNO (h. št. 8a, 11, 16, 17, 28, 33, 33a, 34, 34a, 35, 35a, 39, 39a, 47), "
        "KOT NA POHORJU (h. št. 14, 14a, 20, 21, 24, 26, 30, 31, 32, 33, 34, 37), "
        "LAČNA GORA (h. št. 41, 42, 43, 44, 46), LUKANJA (h. št. 6a), OKOŠKA GORA (h. št. 5), "
        "OPLOTNICA: Šolska ulica (h. št. 30), PLANINA POD ŠUMIKOM (h. št. 3, 4, 4a, 8, 10, 10c, "
        "11, 11a, 11b, 12, 15, 16, 16a, 18, 19, 20b, 22, 23, 24, 25, 27, 28), REP (h. št. 8, 9), "
        "SPODNJA NOVA VAS (h. št. 1a), STARI LOG (h. št. 76, 77), UGOVEC (h. št. 16A), "  # codespell:ignore vas
        "ZLOGONA GORA (h. št. 2a, 2b, 3, 14, 16, 24)"
    ): "dGl2NGQ4dWQ5bDJtcGNjMTRpZnAxajF1Y2tAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "22: BOJTINA (h. št. 1, 2, 5, 7, 9, 11, 14, 15, 16, 18, 19, 21, 33, 34, 35, 40), "
        "FRAJHAJM, KLOPCE (h. št. 27), NOVA GORA NAD SLOV. BISTRICO (h. št. 91, 92, 94), "
        "OŠELJ (h. št. 3b, 30, 30a, 31a), PLANICA (h. št. 26, 31, 32, 33), "
        "SMREČNO (h. št. 4, 4a, 38, 41, 42, 46, 51), SPODNJE PREBUKOVJE (h. št. 17, 21, 22, 24, 26), "
        "ŠMARTNO NA POHORJU (h. št. 30, 32, 41, 42, 43, 44)"
    ): "anNnZ3MzZ3FqbHVidnJiMzhqYzJlOW9kdjRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "23: DOBROVA PRI PRIHOVI (h. št. 10, 10a), FOŠT (h. št. 1a, 2, 3, 3a, 4, 5, 6, 8, "
        "17, 17a, 18, 19, 20), LJUBIČNO (razen h. št. 38 in 40), MODRIČ (h. št. 10, 11), "
        "OKOŠKA GORA (h. št. 21, 24, 24c, 25, 28, 29, 31, 52, 54, 56, 57, 57a, 57c, 58, 59, 60), "
        "PREPUŽ (h. št. 16), PRETREŽ (h. št. 17, 18, 21), PRIHOVA (h. št. 10, 11, 11a, 11b, "
        "18a, 18b, 26, 30, 31), SLOVENSKA BISTRICA: V Črnec (h. št. 9, 15, 20, 21, 23), "
        "STANOVSKO (h. št. 65, 66, 67), STRAŽA PRI OPLOTNICI (h. št. 7, 8, 9, 10, 11, 12, "
        "16, 17, 18, 19), TINJSKA GORA (h. št. 39, 41, 43, 44, 45, 77, 80, 82, 87, 88, 89, "
        "90, 91), VINARJE (h. št. 8, 11, 14, 15, 18, 19a, 100, 101, 102), VISOLE (h. št. 124, "
        "125, 125a, 136, 138, 139, 141, 142, 144, 145, 149, 150, 151, 152, 153a, 155, 159), "
        "ZGORNJA BISTRICA (h. št. 55, 56), ZGORNJE GRUŠOVJE (h. št. 9, 9b), "
        "ZGORNJE POLJČANE: Maistrova ulica (h. št. 23), Ob Beli (h. št. 7), ZLOGONA VAS (h. št. 16)"  # codespell:ignore vas
    ): "djY3bWNxdmNhYnNxMnRiMWZuazliZDYwOGdAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "24: FRAM: Turnerjeva ulica (h. št. 134), MORJE: Na livadi (h. št. 23, 25, 28, 30, 32)"  # codespell:ignore fram
    ): "bW5zaGo1dDM1bjJwa2RwZG42ZmozN3E0aTBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
}

BIO_REGIONS = {
    "Brez odvoza bioloških odpadkov": "",
    (
        "PONEDELJEK: Občina Makole: MAKOLE, MOSTEČNO, PEČKE; "
        "Občina Poljčane: ČADRAMSKA VAS, KRIŽEČA VAS, LUŠEČKA VAS, NOVAKE, "  # codespell:ignore vas
        "POLJČANE, SPODNJA BREŽNICA, SPODNJE POLJČANE, STUDENICE, ZGORNJE POLJČANE"
    ): "aTg3NGo0Y2dzZnU4bGM3NmtvaHY3YjVvZDBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "TOREK: Občina Slovenska Bistrica: BUKOVEC, GABERNIK, KLOPCE, OGLJENŠAK, "
        "SELE PRI POLSKAVI, SLOVENSKA BISTRICA: Jamova ulica, Kopališka ulica, "
        "Mroževa ulica, Ob potoku, Osojna ulica, Prvomajska ulica, Ribiška ulica, "
        "Samova ulica, Šolska ulica, Tomšičeva ulica, Tovarniška ulica, "
        "Ulica Bračičeve brigade, Ulica Pohorskega odreda, SPODNJA POLSKAVA, "
        "ZGORNJA BISTRICA, ZGORNJA POLSKAVA"
    ): "YmM0ZmlxNXJxYWQ3dHNqMDF1bGJuMDVsb2dAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "SREDA: Občina Slovenska Bistrica: CIGONCA, DEVINA, KOVAČA VAS, "  # codespell:ignore vas
        "SLOVENSKA BISTRICA (celo mesto razen ulic, ki se pobirajo v torek), SPODNJA NOVA VAS"  # codespell:ignore vas
    ): "ZzhrYTRrb29sZjZzbms0MDBsa3U1dXBuaDRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "ČETRTEK: Občina Slovenska Bistrica: ČREŠNJEVEC, GAJ PRI PRAGERSKEM, GLADOMES, "
        "KRIŽNI VRH, LAPORJE, LESKOVEC, LOKANJA VAS, PRAGERSKO, PRELOGE, SPODNJA LOŽNICA, "  # codespell:ignore vas
        "SPODNJI GAJ PRI PRAGERSKEM, STARI LOG, VRHLOGA, ZGORNJA LOŽNICA, ŽABLJEK; "
        "Občina Oplotnica: ČADRAM, GORICA PRI OPLOTNICI, LAČNA GORA, MALAHORNA, "
        "MARKEČICA, OPLOTNICA, POBREŽ"
    ): "M25ybDlsY3A5MXE5NjYwdmUwN29vazc0ZjBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
    (
        "PETEK: Občina Rače-Fram: BREZULA, FRAM, JEŠENCA, KOPIVNIK, MORJE, "  # codespell:ignore fram
        "PODOVA, POŽEG, RAČE, RANČE, SPODNJA GORICA, ZGORNJA GORICA"
    ): "cG9iZWhpbzVuYjQ4ODNwcDBuNjJjOHM2dThAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
}


def _cid_to_url(cid: str) -> str:
    cid_padded = cid + "=" * ((4 - len(cid) % 4) % 4)
    decoded_id = base64.b64decode(cid_padded).decode("utf-8")
    encoded_id = urllib.parse.quote(decoded_id)
    return f"https://calendar.google.com/calendar/ical/{encoded_id}/public/basic.ics"


def _get_urls(source: BaseSource, *_, **__) -> list[str]:
    urls = [_cid_to_url(MAIN_REGIONS[source.params["main_region"]])]
    bio_cid = BIO_REGIONS.get(source.params["bio_region"], "")
    if bio_cid:
        urls.append(_cid_to_url(bio_cid))
    return urls


@final
class Source(BaseSource):
    TITLE = "Komunala Slovenska Bistrica"
    DESCRIPTION = "Source for Komunala Slovenska Bistrica."
    URL = "https://www.komunala-slb.si"
    COUNTRY = "si"

    HOWTO: ClassVar[dict] = {
        "sl": (
            "Izberite svoje območje iz seznama urnikov, objavljenih na "
            "https://www.komunala-slb.si/google-koledar.html. "
            "Če vaša lokacija nima ločenega odvoza bioloških odpadkov (ali pa je ta "
            "že vključen v urnikih 16, 17 ali 18), izberite "
            "'Brez odvoza bioloških odpadkov'."
        ),
        "en": (
            "Select your municipality/area from the schedule list published at "
            "https://www.komunala-slb.si/google-koledar.html. "
            "If your area does not have a separate organic waste collection (or if it is already "
            "included in schedules 16, 17, or 18), select 'Brez odvoza bioloških odpadkov'."
        ),
        "de": (
            "Wählen Sie Ihre Gemeinde/Ihr Gebiet aus der unter "  # codespell:ignore sie,unter
            "https://www.komunala-slb.si/google-koledar.html veröffentlichten Liste. "
            "Wenn Ihr Gebiet keine separate Biomüllabfuhr hat (oder diese bereits in den Plänen "  # codespell:ignore oder
            "16, 17 oder 18 enthalten ist), wählen Sie 'Brez odvoza bioloških odpadkov'."  # codespell:ignore oder,ist,sie
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Schedule 5 with Monday BIO": {
            "main_region": list(MAIN_REGIONS.keys())[4],
            "bio_region": list(BIO_REGIONS.keys())[1],
        },
        "Schedule 22 with EMB on Pohorje": {
            "main_region": list(MAIN_REGIONS.keys())[21],
            "bio_region": "Brez odvoza bioloških odpadkov",
        },
        "Schedule 24 with all fractions combined": {
            "main_region": list(MAIN_REGIONS.keys())[23],
            "bio_region": "Brez odvoza bioloških odpadkov",
        },
    }

    PARAMS = (
        dropdown("main_region", options=list(MAIN_REGIONS.keys())),
        dropdown("bio_region", options=list(BIO_REGIONS.keys())),
    )

    retrieve = retrievers.FanOutRetriever(
        targets=_get_urls,
    )
    parse = parsers.EachResponse(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "MKO": wt.GENERAL_WASTE,
            "EMBALAŽA": wt.RECYCLABLES,
            "EMB": wt.RECYCLABLES,
            "PAPIR": wt.PAPER,
            "STEKLO": wt.GLASS,
            "BIO": wt.ORGANIC,
            "VSE FRAKCIJE": [
                wt.GENERAL_WASTE,
                wt.RECYCLABLES,
                wt.PAPER,
                wt.GLASS,
            ],
        }
    )

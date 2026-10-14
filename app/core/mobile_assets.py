# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — telefon eşlik uygulamasının (PWA) statik varlıkları.

Bu modül :mod:`app.core.mobile_server` tarafından sunulan üç sabiti içerir:

* :data:`HTML` — tek sayfalık, Türkçe, koyu temalı telefon arayüzü.
* :data:`MANIFEST` — PWA manifest'i (ana ekrana ekleme için).
* :data:`SW` — en küçük servis işçisi (yalnızca kurulabilirlik için).

Tasarım kuralları:

* **Harici kaynak yok** — font, CDN, resim isteği yapılmaz; her şey bu
  dosyanın içindedir (telefon yalnızca PC'deki sunucuya erişebilir).
* Yerleşim fiziksel plakayı aynalar (4 sütunlu CSS grid; tuş sayımı
  fiziksel plakada SOL ALTTAN başlar). Enkoder ızgaranın altında kendi
  geniş kartındadır — sağda boş sütun kalmaz::

      K9   K10  [COMBO] [OS]
      K5   K6   K7      K8
      K1   K2   K3      K4
      ------- ENKODER -------

* Olaylar ``EventSource('events')`` üzerinden gelir; anahtar adları
  ``app/core/device.py::parse_line`` çıktısıyla birebir aynıdır
  (``key`` → ``number``/``edge``, ``enc`` → ``action`` …).
* iOS Safari ve Android Chrome uyumu: ``-webkit-tap-highlight`` kapalı,
  ``safe-area`` iç boşlukları uygulanır.
"""

from __future__ import annotations

__all__ = ["HTML", "MANIFEST", "SW"]

#: Tek sayfalık telefon arayüzü (Türkçe, koyu tema).
#:
#: ÖNEMLİ: Sayfa içindeki tüm adresler BAĞILDIR ("state", "events",
#: "sw.js", "manifest.webmanifest", ikonlar). Sunucu her şeyi gizli
#: jetonun altında (``/t/<jeton>/``) sunduğu için bağıl adresler
#: jetonu kendiliğinden taşır; kök ("/state") kullanılırsa istek 404
#: alır. Bkz. app/core/mobile_server.py do_GET jeton kapısı.
HTML: str = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1a1a1a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ExtraKeyboard">
<title>ExtraKeyboard</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-192.png">
<link rel="icon" href="icon-192.png">
<style>
:root{
  --arka:#1a1a1a;   /* sayfa arka planı */
  --kart:#212121;   /* kart arka planı */
  --kenar:#2f2f2f;  /* kart kenarlığı */
  --ok:#2CC985;     /* bağlantı tamam */
  --hata:#E04F5F;   /* hata / cihaz yok */
  --combo:#FF9500;  /* combo modu */
  --win:#1E90FF;    /* Windows mavisi */
  --mac:#FFFFFF;    /* macOS beyazı */
  --flas:#3B8ED0;   /* tuş basış flaşı */
  --yazi:#e8e8e8;
  --soluk:#9a9a9a;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
html,body{margin:0;padding:0;background:var(--arka);color:var(--yazi);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-user-select:none;user-select:none;touch-action:manipulation;}
body{min-height:100vh;
  padding:calc(10px + env(safe-area-inset-top)) calc(12px + env(safe-area-inset-right))
          calc(14px + env(safe-area-inset-bottom)) calc(12px + env(safe-area-inset-left));}

/* --- üst durum çubuğu --- */
#durum{display:flex;align-items:center;gap:9px;background:var(--kart);
  border:1px solid var(--kenar);border-radius:12px;padding:10px 14px;margin-bottom:12px;}
#durum-nokta{width:10px;height:10px;border-radius:50%;background:#666;flex:none;
  transition:background .3s,box-shadow .3s;}
#durum-metin{font-size:14px;font-weight:600;color:var(--soluk);transition:color .3s;}
#profil{margin-left:auto;font-size:12px;color:var(--soluk);overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;max-width:40%;}
#durum.bagli #durum-nokta{background:var(--ok);box-shadow:0 0 8px rgba(44,201,133,.8);}
#durum.bagli #durum-metin{color:var(--ok);}
#durum.cihaz-yok #durum-nokta{background:var(--hata);box-shadow:0 0 8px rgba(224,79,95,.8);}
#durum.cihaz-yok #durum-metin{color:var(--hata);}
#durum.sunucu-yok #durum-nokta{background:#666;}
#durum.sunucu-yok #durum-metin{color:var(--soluk);}

/* --- plaka yerleşimi: fiziksel klavyeyi aynalar ---
   3 sıra x 4 sütun (cihazla birebir), tuş sayımı SOL ALTTAN başlar;
   üst sıra soldan sağa: K9, K10, KOMBO, DEĞİŞİM(OS). Enkoder ızgaranın
   ALTINDA kendi geniş kartındadır — böylece sağda boş sütun kalmaz ve
   kartlar telefon ekranında büyür. */
.plaka{display:grid;gap:10px;grid-template-columns:repeat(4,minmax(0,1fr));
  grid-template-areas:
    "k9 k10 combo os"
    "k5 k6 k7 k8"
    "k1 k2 k3 k4";}
#kart-K1{grid-area:k1}#kart-K2{grid-area:k2}#kart-K3{grid-area:k3}
#kart-K4{grid-area:k4}#kart-K5{grid-area:k5}#kart-K6{grid-area:k6}
#kart-K7{grid-area:k7}#kart-K8{grid-area:k8}#kart-K9{grid-area:k9}
#kart-K10{grid-area:k10}
#kart-COMBO{grid-area:combo}#kart-OS{grid-area:os}

/* bölüm başlığı (ızgara ile enkoder arası) */
.bolum-basligi{display:flex;align-items:center;gap:8px;margin:16px 2px 8px;
  font-size:11px;font-weight:700;letter-spacing:1.2px;color:var(--soluk);
  text-transform:uppercase;}
.bolum-basligi::after{content:"";flex:1;height:1px;background:var(--kenar);}

.kart{background:var(--kart);border:1px solid var(--kenar);border-radius:16px;
  padding:12px 6px;min-height:88px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:5px;text-align:center;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,.35);
  transition:box-shadow .3s ease,transform .3s ease,border-color .3s ease,background .3s ease;}
.kart .no{font-size:10px;color:var(--soluk);letter-spacing:.8px;font-weight:700;}
.kart .ad{font-size:13px;font-weight:600;max-width:100%;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;}
.kart .ikon{font-size:20px;line-height:1;}

/* enkoder: ızgaranın altında tam genişlikte, yatay yerleşimli kart */
#kart-ENC{flex-direction:row;justify-content:center;gap:18px;min-height:76px;
  padding:14px 18px;}
#kart-ENC .no{order:1;}
#kart-ENC .enc-satir{order:2;}
#kart-ENC .ad{order:3;font-size:13px;}

/* tuş basılı: parlak mavi glow + hafif küçülme; bırakınca 300 ms sönümlenir */
.kart.basili{border-color:var(--flas);background:#26313c;
  box-shadow:0 0 16px rgba(59,142,208,.75),inset 0 0 5px rgba(59,142,208,.55);
  transform:scale(.96);transition-duration:.05s;}

/* --- enkoder kartı --- */
.enc-satir{display:flex;align-items:center;gap:6px;}
.enc-ok{font-size:20px;line-height:1;opacity:.25;color:var(--soluk);
  transition:opacity .3s ease,color .3s ease;}
.enc-ok.flas{opacity:1;color:var(--flas);transition-duration:.03s;}
.enc-nokta{width:14px;height:14px;border-radius:50%;border:2px solid var(--soluk);
  transition:border-color .3s,box-shadow .3s;}
#kart-ENC.basili .enc-nokta{border-color:var(--flas);
  box-shadow:0 0 10px rgba(59,142,208,.85);}

/* --- combo kartı --- */
#kart-COMBO.aktif{border-color:var(--combo);
  box-shadow:0 0 14px rgba(255,149,0,.55),inset 0 0 5px rgba(255,149,0,.35);}
#kart-COMBO.aktif .ad{color:var(--combo);}
#kart-COMBO.aktif .no{color:var(--combo);}

/* --- OS kartı --- */
.os-etiket{font-size:16px;font-weight:800;letter-spacing:1px;color:var(--soluk);
  transition:color .3s;}
#kart-OS.os-win{border-color:var(--win);
  box-shadow:0 0 10px rgba(30,144,255,.35);}
#kart-OS.os-win .os-etiket{color:var(--win);}
#kart-OS.os-mac{border-color:var(--mac);
  box-shadow:0 0 10px rgba(255,255,255,.28);}
#kart-OS.os-mac .os-etiket{color:var(--mac);}

/* dar ekranlarda (dikey telefon) kartları sıkılaştır */
@media (max-width:430px){
  .plaka{gap:8px;}
  .kart{min-height:78px;border-radius:14px;padding:10px 4px;}
  .kart .ad{font-size:11px;}
  .kart .no{font-size:9px;}
  .enc-ok{font-size:18px;}
  .os-etiket{font-size:15px;}
  #kart-ENC{min-height:68px;gap:14px;padding:12px;}
}

/* çok dar ekranlarda (küçük telefonlar) taşmayı önle */
@media (max-width:360px){
  .plaka{gap:6px;}
  .kart{min-height:70px;padding:8px 3px;}
  .kart .ad{font-size:10px;}
}
</style>
</head>
<body>
<header id="durum" class="sunucu-yok">
  <span id="durum-nokta"></span>
  <span id="durum-metin">Sunucu aranıyor…</span>
  <span id="profil"></span>
</header>

<main class="plaka">
  <div class="kart" id="kart-K1"><div class="no">K1</div><div class="ad" id="ad-K1">Tuş 1</div></div>
  <div class="kart" id="kart-K2"><div class="no">K2</div><div class="ad" id="ad-K2">Tuş 2</div></div>
  <div class="kart" id="kart-K3"><div class="no">K3</div><div class="ad" id="ad-K3">Tuş 3</div></div>
  <div class="kart" id="kart-K10"><div class="no">K10</div><div class="ad" id="ad-K10">Tuş 10</div></div>

  <div class="kart" id="kart-K4"><div class="no">K4</div><div class="ad" id="ad-K4">Tuş 4</div></div>
  <div class="kart" id="kart-K5"><div class="no">K5</div><div class="ad" id="ad-K5">Tuş 5</div></div>
  <div class="kart" id="kart-K6"><div class="no">K6</div><div class="ad" id="ad-K6">Tuş 6</div></div>
  <div class="kart" id="kart-COMBO">
    <div class="no">COMBO</div>
    <div class="ikon" id="combo-ikon">&#128275;</div>
    <div class="ad" id="combo-metin">Kapalı</div>
  </div>

  <div class="kart" id="kart-K7"><div class="no">K7</div><div class="ad" id="ad-K7">Tuş 7</div></div>
  <div class="kart" id="kart-K8"><div class="no">K8</div><div class="ad" id="ad-K8">Tuş 8</div></div>
  <div class="kart" id="kart-K9"><div class="no">K9</div><div class="ad" id="ad-K9">Tuş 9</div></div>
  <div class="kart" id="kart-OS">
    <div class="no">OS</div>
    <div class="os-etiket" id="os-etiket">&mdash;</div>
    <div class="ad" id="os-ad">Bilinmiyor</div>
  </div>
</main>

<div class="bolum-basligi">Enkoder</div>
<div class="kart" id="kart-ENC">
  <div class="no">ENC</div>
  <div class="enc-satir"><span id="enc-sol" class="enc-ok">&#8249;</span><span class="enc-nokta"></span><span id="enc-sag" class="enc-ok">&#8250;</span></div>
  <div class="ad" id="ad-ENC">Enkoder</div>
</div>

<script>
(function () {
  "use strict";

  var durum = document.getElementById("durum");
  var durumMetin = document.getElementById("durum-metin");
  var profilEtiketi = document.getElementById("profil");

  var sunucuBagli = false;  // EventSource açık mı?
  var cihazBagli = false;   // PC, klavyeyi görüyor mu?

  function durumuGuncelle() {
    if (!sunucuBagli) {
      durum.className = "sunucu-yok";
      durumMetin.textContent = "Sunucu aranıyor…";
    } else if (cihazBagli) {
      durum.className = "bagli";
      durumMetin.textContent = "Bağlı";
    } else {
      durum.className = "cihaz-yok";
      durumMetin.textContent = "Cihaz yok";
    }
  }

  /* --- tuş kartları --- */

  function tusBas(no, basili) {
    var kart = document.getElementById("kart-K" + no);
    if (!kart) { return; }
    if (basili) { kart.classList.add("basili"); }
    else { kart.classList.remove("basili"); }
  }

  function kisaBas(no, ms) {
    tusBas(no, true);
    setTimeout(function () { tusBas(no, false); }, ms || 300);
  }

  /* --- enkoder kartı --- */

  function encFlas(yon) {  // yon: "cw" (sağ) | "ccw" (sol)
    var ok = document.getElementById(yon === "cw" ? "enc-sag" : "enc-sol");
    if (!ok) { return; }
    ok.classList.add("flas");
    clearTimeout(ok._zaman);
    ok._zaman = setTimeout(function () { ok.classList.remove("flas"); }, 250);
  }

  function encGlow(uzun) {
    var kart = document.getElementById("kart-ENC");
    if (!kart) { return; }
    kart.classList.add("basili");
    clearTimeout(kart._zaman);
    kart._zaman = setTimeout(function () { kart.classList.remove("basili"); },
                             uzun ? 600 : 300);
  }

  /* --- combo ve OS kartları --- */

  function comboDurum(acik) {
    var kart = document.getElementById("kart-COMBO");
    var ikon = document.getElementById("combo-ikon");
    var metin = document.getElementById("combo-metin");
    if (acik) {
      kart.classList.add("aktif");
      ikon.innerHTML = "&#128274;";   /* kilitli */
      metin.textContent = "Açık";
    } else {
      kart.classList.remove("aktif");
      ikon.innerHTML = "&#128275;";   /* açık kilit */
      metin.textContent = "Kapalı";
    }
  }

  function osDurum(os) {
    var kart = document.getElementById("kart-OS");
    var etiket = document.getElementById("os-etiket");
    var ad = document.getElementById("os-ad");
    var deger = String(os || "").toLowerCase();
    kart.classList.remove("os-win", "os-mac");
    if (!deger) { etiket.innerHTML = "&mdash;"; ad.textContent = "Bilinmiyor"; return; }
    if (deger.indexOf("mac") === 0) {
      kart.classList.add("os-mac");
      etiket.textContent = "MAC";
      ad.textContent = "macOS";
    } else {
      kart.classList.add("os-win");
      etiket.textContent = "WIN";
      ad.textContent = "Windows";
    }
  }

  /* --- durum anlık görüntüsü (/state ve kind=state) --- */

  function durumUygula(s) {
    if (!s || typeof s !== "object") { return; }
    if (typeof s.link === "boolean") { cihazBagli = s.link; durumuGuncelle(); }
    if (s.os) { osDurum(s.os); }
    if (typeof s.combo === "boolean") { comboDurum(s.combo); }
    if (s.profile) { profilEtiketi.textContent = s.profile; }
    var keys = (s.keys && typeof s.keys === "object") ? s.keys : {};
    for (var i = 1; i <= 10; i++) {
      var bilgi = keys["K" + i];
      var ad = document.getElementById("ad-K" + i);
      if (bilgi && ad && bilgi.name) { ad.textContent = bilgi.name; }
    }
    var enc = (s.encoder && typeof s.encoder === "object") ? s.encoder : {};
    var encAd = document.getElementById("ad-ENC");
    if (enc.press && enc.press.name && encAd) { encAd.textContent = enc.press.name; }
  }

  /* --- olay dağıtımı --- */

  function olayIsle(mesaj) {
    if (!mesaj || typeof mesaj !== "object") { return; }
    var kind = mesaj.kind;
    if (kind === "key") {
      var no = (mesaj.number != null) ? mesaj.number : mesaj.key;
      var basili = mesaj.edge ? (mesaj.edge === "down")
                              : (mesaj.state === "down" || mesaj.pressed === true);
      tusBas(no, basili);
    } else if (kind === "combo") {
      if (mesaj.a) { kisaBas(mesaj.a, 300); }
      if (mesaj.b) { kisaBas(mesaj.b, 300); }
    } else if (kind === "mode") {
      comboDurum(mesaj.combo === true || mesaj.state === "on");
    } else if (kind === "os") {
      osDurum(mesaj.os || mesaj.os_raw);
    } else if (kind === "enc") {
      var eylem = mesaj.action || mesaj.slot;
      if (eylem === "cw" || eylem === "ccw") { encFlas(eylem); }
      else if (eylem === "press") { encGlow(false); }
      else if (eylem === "long") { encGlow(true); }
    } else if (kind === "link") {
      cihazBagli = (mesaj.connected === true);
      durumuGuncelle();
    } else if (kind === "state") {
      durumUygula(mesaj);
    }
    /* hb / hello / bye: sessizce yok sayılır */
  }

  /* --- sunucu bağlantısı (SSE) --- */

  var kaynak = null;

  function baglan() {
    if (kaynak) { try { kaynak.close(); } catch (hata) { } }
    kaynak = new EventSource("events");
    kaynak.onopen = function () { sunucuBagli = true; durumuGuncelle(); };
    kaynak.onerror = function () { sunucuBagli = false; durumuGuncelle(); };
    kaynak.onmessage = function (olay) {
      try { olayIsle(JSON.parse(olay.data)); } catch (hata) { }
    };
  }

  baglan();

  /* Uygulama öne dönünce bağlantı tamamen kapandıysa yeniden kur (iOS). */
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && kaynak && kaynak.readyState === 2) { baglan(); }
  });

  /* İlk açılışta adları hemen doldur (SSE gecikirse diye yedek). */
  fetch("state").then(function (yanit) { return yanit.json(); })
                 .then(durumUygula)
                 .catch(function () { });

  /* PWA kurulabilirliği için en küçük servis işçisi. */
  if ("serviceWorker" in navigator) {
    try { navigator.serviceWorker.register("sw.js"); } catch (hata) { }
  }
})();
</script>
</body>
</html>
"""

#: PWA manifest'i — ana ekrana "ExtraKeyboard" olarak eklenir.
MANIFEST: str = """{
  "name": "ExtraKeyboard",
  "short_name": "ExtraKeyboard",
  "description": "ExtraKeyboard MK1 telefon eşlik ekranı",
  "lang": "tr",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#1a1a1a",
  "theme_color": "#1a1a1a",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
"""

#: En küçük servis işçisi — yalnızca PWA kurulabilirliği için; ağdan geçirir.
SW: str = """/* ExtraKeyboard PWA servis işçisi — yalnızca kurulabilirlik için. */
self.addEventListener("install", function (olay) {
  self.skipWaiting();
});
self.addEventListener("activate", function (olay) {
  olay.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", function (olay) {
  /* Ağdan geçir (passthrough) — önbellekleme yapılmaz. */
});
"""

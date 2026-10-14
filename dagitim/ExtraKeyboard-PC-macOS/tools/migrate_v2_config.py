#!/usr/bin/env python3
"""
ExtraKeyboard MK1 — eski v2 yapılandırmasını v3 şemasına taşıyan araç.

Eski ``macro_config.json`` dosyasındaki ``F13``..``F20`` tuş atamalarını ve
``combine`` bölümündeki combo atamalarını, spec bölüm 7'deki şema 3
(``config.json``) biçimine dönüştürür.

Taşıma kuralları
----------------

* ``F13`` -> ``K1``, ``F14`` -> ``K2``, … , ``F20`` -> ``K8``. ``K9`` boş kalır
  (v2'de dokuzuncu tuş yoktu).
* Eski ``combine`` bölümündeki anahtarlar ``C_<a>_<b>`` biçimine çevrilir
  (``a < b``). 0 tabanlı eski indeksler 1 tabanlıya kaydırılır.
* v2'de işletim sistemi ayrımı olmadığı için aynı eylemler hem ``mac`` hem
  ``windows`` profiline yazılır; Windows kopyasında ``command``/``cmd``
  tuşları ``ctrl``'ye çevrilir.
* Enkoder ayarları v2'de yoktu; varsayılan ses eylemleriyle üretilir.

Kullanım
--------

::

    python3 tools/migrate_v2_config.py                 # varsayılan yollar
    python3 tools/migrate_v2_config.py --dry-run       # yazmadan önizle
    python3 tools/migrate_v2_config.py -i eski.json -o yeni.json --force

Çıkış kodları: ``0`` başarı, ``1`` hata, ``2`` kullanıcı iptali / atlandı.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

# Betik doğrudan çalıştırıldığında proje kökünü içe aktarma yoluna ekle.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.core.config import (  # noqa: E402  (yol ayarından sonra içe aktarılmalı)
    COMBO_IDS,
    DEFAULT_PROFILE_NAME,
    KEY_IDS,
    OS_KEYS,
    SCHEMA_VERSION,
    V2_KEY_MAP,
    looks_like_v2,
    migrate_v2_data,
)

__all__ = ["main", "read_legacy", "write_config", "summarize"]


def read_legacy(path: str) -> dict[str, Any]:
    """
    Eski yapılandırma dosyasını okur.

    :param path: ``macro_config.json`` dosyasının yolu.
    :return: Ayrıştırılmış sözlük.
    :raises SystemExit: Dosya yoksa, okunamıyorsa veya geçerli JSON değilse.
    """
    if not os.path.exists(path):
        print(f"HATA: Eski yapılandırma bulunamadı: {path}", file=sys.stderr)
        raise SystemExit(1)

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"HATA: '{path}' okunamadı: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if not isinstance(data, dict) or not data:
        print(f"HATA: '{path}' geçerli bir v2 yapılandırması içermiyor.", file=sys.stderr)
        raise SystemExit(1)

    return data


def write_config(data: dict[str, Any], path: str) -> None:
    """
    Yeni yapılandırmayı atomik olarak diske yazar.

    :param data: Şema 3 sözlüğü.
    :param path: Hedef ``config.json`` yolu.
    :raises SystemExit: Yazma başarısız olursa.
    """
    tmp_path = path + ".tmp"
    try:
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except (OSError, TypeError, ValueError) as exc:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        print(f"HATA: '{path}' yazılamadı: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def summarize(legacy: dict[str, Any], migrated: dict[str, Any]) -> list[str]:
    """
    Taşıma sonucunu insan tarafından okunabilir satırlara döker.

    :param legacy: Eski yapılandırma sözlüğü.
    :param migrated: Üretilen yeni yapılandırma sözlüğü.
    :return: Ekrana yazdırılacak Türkçe satırlar.
    """
    lines: list[str] = []
    profile = migrated["profiles"][DEFAULT_PROFILE_NAME]

    moved_keys = 0
    for old_key, new_key in V2_KEY_MAP.items():
        source = legacy.get(old_key)
        if not isinstance(source, dict):
            continue
        action = profile["mac"]["keys"][new_key]
        if action.get("type", "none") == "none" and not action.get("value"):
            continue
        moved_keys += 1
        lines.append(
            f"  {old_key} -> {new_key}: {action['type']} = {action['value']!r} ({action['name']})"
        )

    combine = legacy.get("combine")
    moved_combos = 0
    if isinstance(combine, dict):
        for cid in COMBO_IDS:
            action = profile["mac"]["combos"][cid]
            if action.get("type", "none") == "none" and not action.get("value"):
                continue
            moved_combos += 1
            lines.append(f"  combo -> {cid}: {action['type']} = {action['value']!r}")

    header = [
        f"Şema sürümü          : {migrated['schema']} (beklenen {SCHEMA_VERSION})",
        f"Profil               : {DEFAULT_PROFILE_NAME}",
        f"İşletim sistemleri   : {', '.join(OS_KEYS)}",
        f"Tuş slotu            : {len(KEY_IDS)} adet ({KEY_IDS[0]}..{KEY_IDS[-1]})",
        f"Combo slotu          : {len(COMBO_IDS)} adet ({COMBO_IDS[0]}..{COMBO_IDS[-1]})",
        f"Taşınan dolu tuş     : {moved_keys}",
        f"Taşınan dolu combo   : {moved_combos}",
    ]
    if lines:
        header.append("Ayrıntılar:")
    return header + lines


def build_parser() -> argparse.ArgumentParser:
    """
    Komut satırı ayrıştırıcısını kurar.

    :return: Yapılandırılmış ``ArgumentParser`` nesnesi.
    """
    parser = argparse.ArgumentParser(
        prog="migrate_v2_config.py",
        description="Eski macro_config.json dosyasını yeni config.json (şema 3) biçimine taşır.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Örnek: python3 tools/migrate_v2_config.py --dry-run",
    )
    parser.add_argument(
        "-i",
        "--input",
        default=str(_PROJECT_ROOT / "macro_config.json"),
        help="Eski v2 yapılandırma dosyası (varsayılan: <proje>/macro_config.json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(_PROJECT_ROOT / "config.json"),
        help="Üretilecek v3 yapılandırma dosyası (varsayılan: <proje>/config.json)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Hedef dosya varsa sormadan üzerine yaz (yedeği .bak olarak alınır)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Hiçbir dosya yazma, yalnızca sonucu ekrana yaz",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Üzerine yazarken .bak yedeği alma",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Aracın giriş noktası.

    :param argv: Komut satırı argümanları (``None`` ise ``sys.argv`` kullanılır).
    :return: Çıkış kodu (0 başarı, 1 hata, 2 atlandı).
    """
    args = build_parser().parse_args(argv)

    input_path = os.path.abspath(os.path.expanduser(args.input))
    output_path = os.path.abspath(os.path.expanduser(args.output))

    print("ExtraKeyboard MK1 — v2 -> v3 yapılandırma taşıma aracı")
    print(f"Kaynak : {input_path}")
    print(f"Hedef  : {output_path}")
    print("-" * 60)

    legacy = read_legacy(input_path)

    if not looks_like_v2(legacy):
        if int(legacy.get("schema", 0) or 0) >= SCHEMA_VERSION:
            print("Kaynak dosya zaten şema 3 biçiminde; taşımaya gerek yok.")
            return 2
        print(
            "UYARI: Kaynak dosya beklenen v2 biçimine benzemiyor "
            "(F13..F20 anahtarları yok). Yine de taşıma denenecek."
        )

    migrated = migrate_v2_data(legacy)

    for line in summarize(legacy, migrated):
        print(line)
    print("-" * 60)

    if args.dry_run:
        print("Önizleme modu (--dry-run): hiçbir dosya yazılmadı.")
        return 0

    if os.path.exists(output_path) and not args.force:
        print(
            f"HATA: '{output_path}' zaten var. Üzerine yazmak için --force kullanın.",
            file=sys.stderr,
        )
        return 1

    if os.path.exists(output_path) and not args.no_backup:
        backup_path = output_path + ".bak"
        try:
            shutil.copy2(output_path, backup_path)
            print(f"Mevcut dosyanın yedeği alındı: {backup_path}")
        except OSError as exc:
            print(f"UYARI: Yedek alınamadı: {exc}", file=sys.stderr)

    write_config(migrated, output_path)
    print(f"TAMAM: Yeni yapılandırma yazıldı -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

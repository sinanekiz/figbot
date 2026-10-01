"""Build the Rev-G two-arm prototype cost extract from the rover BOM."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "bom" / "FLAT_GROUND_ROVER_P0.csv"
OUTPUT = ROOT / "bom" / "REV_G_ARM_COST_ESTIMATE.csv"
REPORT = ROOT / "reports" / "REV_G_ARM_COST_ESTIMATE.md"


def build() -> tuple[float, float]:
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["part_id"].startswith("P0-ARM-")]
    two_arm_total = sum(float(row["line_total_try"]) for row in rows if row["line_total_try"])
    one_arm_equivalent = two_arm_total / 2
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    report = [
        "# Rev-G iki kollu prototip maliyet özeti",
        "",
        "Durum: **KARIŞIK GÜNCEL FİYAT + TAHMİN / TEKLİF DEĞİLDİR**",
        "",
        f"- İki kol için çalışma toplamı: **{two_arm_total:,.2f} TL**",
        f"- Kol başına aritmetik karşılık: **{one_arm_equivalent:,.2f} TL**",
        f"- Üç araç / altı kol için aritmetik karşılık: **{two_arm_total * 3:,.2f} TL**",
        "",
        "Bu tutar sekiz MG996R, iki MG90S sınıfı kavrayıcı servosu, iki mekanik kol seti, iki karşı denge seti, bir yüksek akım DC/DC ve bir PWM kontrol kartı içerir. Her kolda J2 omuz eklemi iki MG996R ile tahrik edilir. Mekanik set, karşı denge, DC/DC ve PWM kartı satıcı teklifi alınmamış tahminlerdir. İşçilik, başarısız baskılar, yedek servo, kargo ve test kaybı dahil değildir.",
        "",
        "MG996R ve MG90S fiyatları satın alma kararı verileceği gün stok, KDV ve ürün orijinalliğiyle yeniden kontrol edilmelidir.",
    ]
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    return two_arm_total, one_arm_equivalent


if __name__ == "__main__":
    print(build())

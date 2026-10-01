"""Compare Rev-C and Rev-G planar pick-to-drop geometry.

This is a deterministic packaging metric, not a dynamic cycle-time or safety
simulation. All coordinates are millimetres in the P0 vehicle frame.
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path
from statistics import mean

from cad.config import parameters as p
from cad.rover.geometry_checks import clearance_report


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports" / "P0_REV_G_LIGHTWEIGHT_ARM_LAYOUT.csv"
REPORT_PATH = ROOT / "reports" / "P0_REV_G_LIGHTWEIGHT_ARM_LAYOUT_REPORT.md"
SEED = 20260902


def _angle_delta_deg(a: float, b: float) -> float:
    return abs(math.degrees((a - b + math.pi) % (2 * math.pi) - math.pi))


def _metrics(target: tuple[float, float], arm: tuple[float, float], drop: tuple[float, float]) -> tuple[float, float]:
    pick_to_drop = math.dist(target, drop)
    pick_angle = math.atan2(target[1] - arm[1], target[0] - arm[0])
    drop_angle = math.atan2(drop[1] - arm[1], drop[0] - arm[0])
    return pick_to_drop, _angle_delta_deg(pick_angle, drop_angle)


def evaluate(count: int = 100) -> tuple[list[dict[str, float | str]], dict[str, float]]:
    rng = random.Random(SEED)
    old_arm = (105.0, 0.0)
    old_drop = (-125.0, 0.0)
    rows: list[dict[str, float | str]] = []
    for index in range(count):
        target = (
            rng.uniform(*p.P0_GROUND_PICK_X_RANGE),
            rng.uniform(*p.P0_GROUND_PICK_Y_RANGE),
        )
        arm_index = 0 if target[1] >= 0 else 1
        new_arm = p.P0_ARM_BASES[arm_index]
        new_drop_xyz = p.P0_BASKET_DROP_POINTS[arm_index]
        new_drop = (new_drop_xyz[0], new_drop_xyz[1])
        old_distance, old_yaw = _metrics(target, old_arm, old_drop)
        new_distance, new_yaw = _metrics(target, new_arm, new_drop)
        rows.append(
            {
                "target_id": f"P0-{index + 1:03d}",
                "target_x_mm": target[0],
                "target_y_mm": target[1],
                "assigned_arm": "left" if arm_index == 0 else "right",
                "rev_c_pick_to_drop_mm": old_distance,
                "rev_f_pick_to_drop_mm": new_distance,
                "rev_c_yaw_swing_deg": old_yaw,
                "rev_f_yaw_swing_deg": new_yaw,
            }
        )
    summary = {
        "old_mean_distance": mean(float(row["rev_c_pick_to_drop_mm"]) for row in rows),
        "new_mean_distance": mean(float(row["rev_f_pick_to_drop_mm"]) for row in rows),
        "old_mean_yaw": mean(float(row["rev_c_yaw_swing_deg"]) for row in rows),
        "new_mean_yaw": mean(float(row["rev_f_yaw_swing_deg"]) for row in rows),
    }
    summary["distance_reduction_pct"] = 100 * (1 - summary["new_mean_distance"] / summary["old_mean_distance"])
    summary["yaw_reduction_pct"] = 100 * (1 - summary["new_mean_yaw"] / summary["old_mean_yaw"])
    return rows, summary


def _write_csv(rows: list[dict[str, float | str]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow({key: f"{value:.3f}" if isinstance(value, float) else value for key, value in row.items()})


def _write_report(summary: dict[str, float]) -> None:
    clearances = clearance_report()
    old_volume = 300.0 * 270.0 * 105.0
    new_volume = p.P0_BASKET_LENGTH * p.P0_BASKET_WIDTH * p.P0_BASKET_HEIGHT
    lines = [
        "# P0 Rev-G hafif çift kol / eğimli ön sepet yerleşim değerlendirmesi",
        "",
        "Durum: **DİJİTAL YERLEŞİM ÇALIŞMASI / PHYSICAL VALIDATION REQUIRED**",
        "",
        "## Karar",
        "",
        "Rev-G, sepeti aracın ön-orta bölümünde tutar ve iki hafif kolu sol ve sağ yanına yerleştirir. Her kolda karşısındaki sepet ön-yan duvarında 150 mm uzunluğunda bırakma açıklığı vardır. Taban önde yüksek, arkada alçaktır; ürünün pasif olarak arkaya ilerleyip sepeti arkadan doldurması amaçlanır. Kamera daha geniş bir alanı görebilir, ancak kol komutu yalnız araç hedefi ilgili yan toplama şeridine hizaladıktan sonra verilir.",
        "",
        "## Sayısal yerleşim karşılaştırması",
        "",
        "100 sabit tohumlu hedef üzerinde yalnız plan görünüşündeki pick-to-drop doğru mesafesi ve taban yaw açısı karşılaştırılmıştır. Dikey hareket, gerçek eklem dinamiği, kavrama, algılama, ürün düşüşü ve iki kolun birbirini beklemesi bu metrikte yoktur.",
        "",
        "| Metrik | Rev-C tek kol / arka sepet | Rev-G eğimli ön sepet / yanlarda iki hafif kol | Değişim |",
        "|---|---:|---:|---:|",
        f"| Ortalama pick-to-drop mesafesi | {summary['old_mean_distance']:.1f} mm | {summary['new_mean_distance']:.1f} mm | %{summary['distance_reduction_pct']:.1f} daha kısa |",
        f"| Ortalama taban yaw hareketi | {summary['old_mean_yaw']:.1f}° | {summary['new_mean_yaw']:.1f}° | %{summary['yaw_reduction_pct']:.1f} daha az |",
        f"| Nominal ana sepet dış hacim oranı | 1.00 | {new_volume / old_volume:.2f} | Kullanılabilir hacim ayrıca ölçülecek |",
        "",
        "## Rev-G kontrollü paket ölçüleri",
        "",
        f"- Kol tabanları: `({p.P0_ARM_BASE_X:.0f}, +{p.P0_ARM_BASE_Y_OFFSET:.0f}, {p.P0_ARM_BASE_Z:.0f})` ve `({p.P0_ARM_BASE_X:.0f}, -{p.P0_ARM_BASE_Y_OFFSET:.0f}, {p.P0_ARM_BASE_Z:.0f})` mm; iki kol sepetin sol ve sağ yanındadır.",
        f"- Ana sepet: `{p.P0_BASKET_LENGTH:.0f} x {p.P0_BASKET_WIDTH:.0f} x {p.P0_BASKET_HEIGHT:.0f} mm`, merkez `({p.P0_BASKET_CENTER_X:.0f}, 0) mm`, taban Z=`{p.P0_BASKET_BOTTOM_Z:.0f} mm`.",
        f"- Sepet tabanı önden arkaya `{p.P0_BASKET_FLOOR_SLOPE_DEG:.1f}°` eğimlidir (`ESTIMATE`); prototip ayar aralığı `{p.P0_BASKET_FLOOR_SLOPE_RANGE_DEG[0]:.0f}–{p.P0_BASKET_FLOOR_SLOPE_RANGE_DEG[1]:.0f}°`, toplam düşüş `{p.P0_BASKET_FRONT_FLOOR_Z - p.P0_BASKET_BOTTOM_Z:.1f} mm`dir.",
        f"- Ön-yan bırakma açıklıklarının merkezi X=`{p.P0_BASKET_SIDE_OPENING_CENTER_X:.0f} mm`; nominal bırakma noktaları X=`{p.P0_BASKET_DROP_POINTS[0][0]:.0f} mm`dir.",
        f"- İlk kol-komut şeritleri X=`{p.P0_ARM_PICK_X_RANGE[0]:.0f}..{p.P0_ARM_PICK_X_RANGE[1]:.0f} mm`, sol Y=`{p.P0_LEFT_ARM_PICK_Y_RANGE[0]:.0f}..{p.P0_LEFT_ARM_PICK_Y_RANGE[1]:.0f} mm`, sağ Y=`{p.P0_RIGHT_ARM_PICK_Y_RANGE[0]:.0f}..{p.P0_RIGHT_ARM_PICK_Y_RANGE[1]:.0f} mm`dir; diğer algılamalar araç yeniden konumlandırması ister.",
        f"- Sepetin ön yüzü X=`{p.P0_BASKET_CENTER_X + p.P0_BASKET_LENGTH / 2:.0f} mm` konumundadır; şasi önüne yalnız `{clearances['basket_front_to_frame_mm']:.1f} mm` kalır.",
        f"- Sepet yan duvarı ile kol adaptörünün iç kenarı arasında `{clearances['basket_side_to_arm_mount_mm']:.1f} mm`; kol adaptörü ile ön teker süpürmesi arasında `{clearances['arm_mount_to_front_wheel_sweep_mm']:.1f} mm` hesaplanmıştır.",
        "",
        "## Hız hedefi açısından anlamı",
        "",
        "İlk hedef 30 nesne/dakika/araçtır; kusursuz paralel paylaşımda her kol en fazla 4.0 s ortalama tam çevrim yapmalıdır. Eski 50-100/dakika hedefi daha sonraki bir stretch çalışmasıdır. Mevcut analitik model bu süreleri göstermemektedir. Rev-G hareket mesafesini ve paralel çalışma olanağını iyileştirir, fakat fiziksel çevrim hedefini doğrulamaz.",
        "",
        "## Zorunlu sonraki kontroller",
        "",
        "- İki gerçek kol STEP'inin tüm eklem aralığında birbirine, ön sepete, kameraya ve tekerlere dinamik çarpışma taraması.",
        "- Y=0 yakınındaki ortak hedefler için bölge sahipliği; bırakma ağızları ayrı olsa da üst çalışma hacimleri kesiştiğinde karşılıklı yazılım kilidi.",
        "- Dolu sepet ve iki kol ile ağırlık merkezi, devrilme, frenleme ve şasi sehim testi.",
        "- Alçak yan açıklıkların gerçek ürün ve kavrayıcı için erişim, sıkışma, sekme ve yumuşak astar testi.",
        "- Düzensiz ürünlerin 5–12° eğimli değiştirilebilir astar üzerinde arkaya ilerlemesi; durma, üst üste binme, darbe ve ezilme testi.",
        "- Tek merkez kameranın iki kol tarafından örtülmesi; gerekirse iki dış kamera veya zamanlamalı görüntü alma karşılaştırması.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, summary = evaluate()
    _write_csv(rows)
    _write_report(summary)
    print(f"wrote {CSV_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"distance_reduction={summary['distance_reduction_pct']:.1f}% yaw_reduction={summary['yaw_reduction_pct']:.1f}%")


if __name__ == "__main__":
    main()

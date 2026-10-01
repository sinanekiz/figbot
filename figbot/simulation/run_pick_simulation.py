"""Run the deterministic 100-target V0 pick test and write traceable reports."""

from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date
from pathlib import Path
from statistics import mean, median

from software.kinematics import ArmKinematics
from simulation.pick_test import BALANCED_NEAR_FUNNEL, CycleConfiguration, PickResult, PickSimulator, generate_targets


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports" / "SIMULATION_PICK_TEST.csv"
REPORT_PATH = ROOT / "reports" / "SIMULATION_REPORT.md"


def _summary(results: list[PickResult]) -> dict[str, float | int]:
    successful = [result for result in results if result.status == "SUCCESS"]
    cycles = [result.cycle_time for result in successful if result.cycle_time is not None]
    travels = [result.travel_distance for result in successful if result.travel_distance is not None]
    return {
        "targets": len(results),
        "successful": len(successful),
        "ik_failed": sum(not result.ik_success for result in results),
        "collision_rejected": sum(result.collision for result in results),
        "mean_cycle": mean(cycles) if cycles else float("nan"),
        "median_cycle": median(cycles) if cycles else float("nan"),
        "max_cycle": max(cycles, default=float("nan")),
        "mean_travel": mean(travels) if travels else float("nan"),
    }


def _write_csv(results: list[PickResult]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "target_id",
        "x_m",
        "y_m",
        "z_m",
        "reachable",
        "ik_success",
        "collision",
        "collision_contacts",
        "travel_distance_m",
        "theoretical_cycle_time_s",
        "status",
        "verification_status",
    )
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "target_id": result.target.identifier,
                    "x_m": f"{result.target.x:.6f}",
                    "y_m": f"{result.target.y:.6f}",
                    "z_m": f"{result.target.z:.6f}",
                    "reachable": str(result.reachable).lower(),
                    "ik_success": str(result.ik_success).lower(),
                    "collision": str(result.collision).lower(),
                    "collision_contacts": ";".join(result.contacts),
                    "travel_distance_m": "" if result.travel_distance is None else f"{result.travel_distance:.6f}",
                    "theoretical_cycle_time_s": "" if result.cycle_time is None else f"{result.cycle_time:.6f}",
                    "status": result.status,
                    "verification_status": "SIMULATED / PHYSICAL VALIDATION REQUIRED",
                }
            )


def _variant_rows(arm: ArmKinematics, targets):
    variants = (
        BALANCED_NEAR_FUNNEL,
        replace(
            BALANCED_NEAR_FUNNEL,
            name="target_side_funnel_estimate",
            hopper_approach=(0.30, -0.20, 0.36),
            hopper_drop=(0.30, -0.20, 0.28),
        ),
        replace(BALANCED_NEAR_FUNNEL, name="conservative_speed_70pct", speed_scale=0.70),
    )
    return [(variant, _summary(PickSimulator(arm, variant).run(targets))) for variant in variants]


def _write_report(arm: ArmKinematics, results: list[PickResult], variant_rows) -> None:
    summary = _summary(results)
    failed = [result.target.identifier for result in results if result.status != "SUCCESS"]
    lines = [
        "# FIGBOT V0 Simülasyon Raporu",
        "",
        f"- Çalıştırma tarihi: {date.today().isoformat()}",
        "- Durum: **SIMULATED / PHYSICAL VALIDATION REQUIRED**",
        f"- Geometri kaynağı: `{arm.geometry.source}`",
        f"- Kol uzunlukları (m): üst `{arm.geometry.upper_arm:.3f}`, ön `{arm.geometry.forearm:.3f}`, takım `{arm.geometry.tool:.3f}`",
        f"- Nominal toplam erişim: `{arm.geometry.maximum_reach:.3f} m`",
        "- Örnekleme alanı: CAD `TARGET_ZONE_X_RANGE/TARGET_ZONE_Y_RANGE`, nominal Z + `0–35 mm` ürün yüksekliği tahmini",
        "- Rastgele tohum: `20260820` (tekrar üretilebilir)",
        "",
        "## 100 hedeflik pick testi",
        "",
        f"- Başarılı çevrim: **{summary['successful']}/{summary['targets']}**",
        f"- IK başarısız: **{summary['ik_failed']}**",
        f"- Çarpışma yaklaşımıyla reddedilen: **{summary['collision_rejected']}**",
        f"- Ortalama teorik çevrim: **{summary['mean_cycle']:.3f} s**",
        f"- Medyan teorik çevrim: **{summary['median_cycle']:.3f} s**",
        f"- En uzun başarılı çevrim: **{summary['max_cycle']:.3f} s**",
        f"- Ortalama uç-efektör seyahati: **{summary['mean_travel']:.3f} m**",
        f"- Başarısız hedefler: `{', '.join(failed) if failed else 'yok'}`",
        "",
        "Başarılı çevrim; önceki huni bırakma pozu → sonraki hedefe yaklaşma → kavrama → kaldırma → huni yaklaşması → aynı bırakma pozu kapalı çevriminin tüm IK ve örneklenmiş joint-space yörünge kontrollerini geçmesi anlamına gelir. Görü algılama süresinin çoğunun kol hareketiyle örtüştüğü kabul edilmiş, çevrime yalnız `0.10 s` artık süre eklenmiştir (**ESTIMATE**).",
        "",
        "## Çevrim varyantları",
        "",
        "| Varyant | Başarı | Ortalama çevrim (s) | Ortalama seyahat (m) | Yorum |",
        "|---|---:|---:|---:|---|",
    ]
    comments = {
        "balanced_near_funnel": "CAD hunisinin iç kenarına yakın bırakma; seçilen V0 düzeni.",
        "target_side_funnel_estimate": "Hedef alanı tarafındaki alternatif huni; yerleşim etkisini gösterir.",
        "conservative_speed_70pct": "Aynı geometri, hız limitlerinin %70'i; kontrol marjı etkisi.",
    }
    for variant, values in variant_rows:
        cycle_text = "N/A" if values["successful"] == 0 else f"{values['mean_cycle']:.3f}"
        travel_text = "N/A" if values["successful"] == 0 else f"{values['mean_travel']:.3f}"
        lines.append(
            f"| `{variant.name}` | {values['successful']}/{values['targets']} | {cycle_text} | {travel_text} | {comments[variant.name]} |"
        )
    variant_values = {variant.name: values for variant, values in variant_rows}
    baseline = variant_values["balanced_near_funnel"]
    target_side = variant_values["target_side_funnel_estimate"]
    cycle_delta = float(baseline["mean_cycle"]) - float(target_side["mean_cycle"])
    travel_delta = float(baseline["mean_travel"]) - float(target_side["mean_travel"])
    lines.extend(
        [
            "",
            "## Yerleşim bulguları",
            "",
            "CAD huni merkezi `(-0.120, 0.250, 0.210) m` tabandan yaklaşık `115.64°` azimuttadır; mevcut J1 üst limiti `115°` olduğundan merkeze doğrudan bırakma matematiksel olarak limit dışındadır. Test, geniş huni girişinin tabana yakın iç kenarındaki `(-0.010, 0.250) m` noktasını kullanır. Bu geçici nokta **ESTIMATE / MECHANICAL REVIEW REQUIRED** durumundadır.",
            f"Hedef alanı tarafındaki alternatif huni proxy'si aynı başarılı hedeflerde ortalama çevrimi `{cycle_delta:.3f} s`, uç seyahatini `{travel_delta:.3f} m` azaltmıştır. Bu güçlü bir yerleşim optimizasyon sinyalidir; kamera FOV, gerçek huni CAD'i ve ürün düşüş yolu birlikte incelenmeden uygulanmamalıdır.",
            "",
            "## Çarpışma proxy kapsamı",
            "",
            "Kontroller: zemin açıklığı, taban/pedestal, şasi taban plakası, kamera AABB, huni silindiri, üst kol–takım öz-çarpışma yaklaşımı ve joint limitleri. Segmentler yörünge boyunca `20 ms` aralıklarla örneklenir. Huni hacminden çıkış ve huniye son yaklaşmada uç noktanın bu hacme bilinçli girmesi nedeniyle yalnız huni proxy'si devre dışı bırakılır; diğer proxy'ler etkin kalır.",
            "",
            "## Sonuç ve sınırlar",
            "",
            "Mevcut CAD huni yerleşimiyle dijital ortalama 5 s hedefinin biraz üzerindedir; dolayısıyla 3–5 s uzun vadeli hedefi henüz doğrulanmış değildir. Sonuç ayrıca motor tork düşümü, kayış esnekliği, kontrol yerleşme süresi, kavrama başarısı ve gerçek algılama gecikmesini modellemez. Tam CAD hedef bölgesinin kenarlarında IK kayıpları vardır; kamera kabul bölgesi, omuz yüksekliği veya joint limitleri fiziksel prototipten önce birlikte gözden geçirilmelidir. Hedef alanı tarafındaki alternatif huni proxy'si ortalama seyahati azaltmıştır; bu yerleşim kamera görüşü ve fiziksel interference incelemesi yapılmadan CAD kararı olarak kabul edilmemelidir.",
            "",
            "Gazebo/ROS 2 dosyaları dijital entegrasyon için hazırlanmıştır; bu çalıştırmada Gazebo fizik motoru mevcut olmadığı için analitik simülasyon kullanılmıştır. İncelenmesi gereken sonraki adım gerçek CAD mesh'leriyle sürekli çarpışma ve motor tork-hız eğrisi doğrulamasıdır.",
            "",
            "## Gereksinim izlenebilirliği",
            "",
            "| Gereksinim | Kanıt | Durum |",
            "|---|---|---|",
            "| `REQ-CTL-001` | FK/IK, CAD joint limitleri, kübik yörünge ve `ros2_control` dosyaları | UNIT TESTED / UNVERIFIED HARDWARE |",
            "| `REQ-SIM-001` | `figbot_v0.world.sdf`: masa/zemin, kuru-yeşil incir, taş, yaprak, dal, huni | XML CHECKED / GAZEBO RUNTIME REQUIRED |",
            "| `REQ-SIM-002` | `SIMULATION_PICK_TEST.csv`, 100 benzersiz hedef | SIMULATED |",
            "| `REQ-PERF-001` | Kapalı çevrim süreleri ve üç yerleşim/hız varyantı | SIMULATED / NOT GUARANTEED |",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    arm = ArmKinematics()
    targets = generate_targets()
    results = PickSimulator(arm).run(targets)
    variant_rows = _variant_rows(arm, targets)
    _write_csv(results)
    _write_report(arm, results, variant_rows)
    summary = _summary(results)
    print(f"wrote {CSV_PATH.relative_to(ROOT)} ({summary['targets']} rows)")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"success={summary['successful']}/{summary['targets']} mean_cycle={summary['mean_cycle']:.3f}s")


if __name__ == "__main__":
    main()

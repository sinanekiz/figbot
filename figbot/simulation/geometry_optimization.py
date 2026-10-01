"""Compare arm lengths and export a 3D reachability point cloud."""

from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date
from pathlib import Path
from statistics import mean

from software.kinematics import ArmKinematics, load_arm_geometry
from software.kinematics.workspace import sample_reachability_cloud
from simulation.pick_test import PickSimulator, generate_targets


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "simulation" / "results"
REPORT_PATH = ROOT / "reports" / "ARM_GEOMETRY_OPTIMIZATION.md"


def _variant(name: str, upper: float, fore: float, tool: float):
    return name, replace(
        load_arm_geometry(),
        upper_arm=upper,
        forearm=fore,
        tool=tool,
        source=f"simulation variant {name}",
        verification_status="ESTIMATE / SIMULATED / PHYSICAL VALIDATION REQUIRED",
    )


VARIANTS = (
    _variant("compact_520", 0.255, 0.205, 0.060),
    _variant("short_560", 0.275, 0.220, 0.065),
    _variant("cad_baseline_605", 0.300, 0.220, 0.085),
    _variant("long_650", 0.320, 0.245, 0.085),
)


def _mass_and_torque(geometry):
    # Rectangular 30x20x2 mm aluminium tube, 2700 kg/m3 from CAD assumptions.
    area_m2 = (30.0 * 20.0 - 26.0 * 16.0) * 1e-6
    linear_density = area_m2 * 2700.0
    upper_mass = geometry.upper_arm * linear_density
    fore_mass = geometry.forearm * linear_density
    wrist_mass_estimate = 0.12
    gripper_payload = 0.22 + 0.10
    distal_mass = wrist_mass_estimate + gripper_payload
    g = 9.80665
    l1, l2, l3 = geometry.upper_arm, geometry.forearm, geometry.tool
    gravity_torque = g * (
        upper_mass * l1 / 2
        + fore_mass * (l1 + l2 / 2)
        + distal_mass * (l1 + l2 + l3)
    )
    inertia_estimate = (
        upper_mass * l1 * l1 / 3
        + fore_mass * (l1 * l1 + l1 * l2 + l2 * l2 / 3)
        + distal_mass * (l1 + l2 + l3) ** 2
    )
    acceleration_torque = inertia_estimate * geometry.joint_limits[1].max_acceleration
    return upper_mass + fore_mass + distal_mass, gravity_torque, acceleration_torque


def _evaluate():
    targets = generate_targets()
    rows = []
    for name, geometry in VARIANTS:
        arm = ArmKinematics(geometry)
        target_ik = sum(arm.inverse(target.x, target.y, target.z, tool_pitch=-1.5707963267948966).success for target in targets)
        results = PickSimulator(arm).run(targets)
        success = [result for result in results if result.status == "SUCCESS"]
        mass, gravity, acceleration = _mass_and_torque(geometry)
        rows.append(
            {
                "variant": name,
                "reach_m": geometry.maximum_reach,
                "target_ik": target_ik,
                "success": len(success),
                "reach_fraction": len(success) / len(results),
                "moving_mass_estimate_kg": mass,
                "j2_gravity_torque_nm": gravity,
                "j2_acceleration_torque_nm": acceleration,
                "j2_peak_no_sf_nm": gravity + acceleration,
                "mean_cycle_s": mean(result.cycle_time for result in success if result.cycle_time is not None) if success else None,
            }
        )
    return rows


def _write_point_cloud(arm: ArmKinematics) -> int:
    points = sample_reachability_cloud(arm)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / "reachability_map.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("x_m", "y_m", "z_m", "status"))
        writer.writerows((f"{x:.6f}", f"{y:.6f}", f"{z:.6f}", "REACHABLE") for x, y, z in points)
    ply_path = RESULTS_DIR / "reachability_map.ply"
    with ply_path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("ply\nformat ascii 1.0\n")
        handle.write(f"element vertex {len(points)}\n")
        handle.write("property float x\nproperty float y\nproperty float z\nend_header\n")
        for x, y, z in points:
            handle.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
    return len(points)


def _write_report(rows, point_count: int) -> None:
    lines = [
        "# FIGBOT Kol Geometrisi Optimizasyonu",
        "",
        f"- Tarih: {date.today().isoformat()}",
        "- Durum: **CALCULATED + SIMULATED / PHYSICAL VALIDATION REQUIRED**",
        "- Hedef popülasyonu: `SIMULATION_PICK_TEST` ile aynı 100 nokta ve `20260820` tohumu",
        "- Hedef kutusu: CAD x `0.12–0.50 m`, y `-0.30–0.30 m`, nominal z `0.020 m` + `0–35 mm` ürün yüksekliği tahmini",
        "",
        "## Sonuçlar",
        "",
        "| Varyant | Nominal erişim (mm) | Hedef IK / 100 | Tam çevrim / 100 | Tahmini hareketli kütle (kg) | J2 yerçekimi (Nm) | J2 ivme (Nm) | J2 toplam, SF yok (Nm) | Ort. çevrim (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        cycle_text = "N/A" if row["mean_cycle_s"] is None else f"{row['mean_cycle_s']:.3f}"
        lines.append(
            f"| `{row['variant']}` | {row['reach_m'] * 1000:.0f} | {row['target_ik']} | {row['success']} | {row['moving_mass_estimate_kg']:.3f} | {row['j2_gravity_torque_nm']:.3f} | {row['j2_acceleration_torque_nm']:.3f} | {row['j2_peak_no_sf_nm']:.3f} | {cycle_text} |"
        )
    lines.extend(
        [
            "",
            "## 550–650 mm gerçekten gerekli mi?",
            "",
            "520 mm sınıfı kol hedef kutusunun tamamını kapsamaz. 560 mm varyantı ağırlık ve torku düşürse de kenar hedeflerde belirgin erişim/joint-limit kaybı bırakır. CAD taban çizgisindeki 605 mm nominal erişim yüksek kapsamayı daha düşük torkla dengeler. 650 mm varyantı bazı dış hedefleri kazanabilir, ancak sabit joint limitleri ve aşağı bakan takım yönelimi nedeniyle uzunluk tek başına tam kapsama sağlamaz; ayrıca hareketli kütle ve J2 torku artar. Bu nedenle **605 mm CAD taban çizgisinin V0 için korunması**, kamera kabul bölgesinin fiziksel testte ölçülmesi ve kaçan kenar hedeflere göre 650 mm seçeneğinin yalnız gerekirse yeniden değerlendirilmesi önerilir.",
            "",
            "Bu karar hedef kutusuna bağlıdır. Kamera kalibrasyonu x/y sınırlarını veya omuz yüksekliğini değiştirirse analiz yeniden üretilmelidir.",
            "",
            "## Hesap varsayımları",
            "",
            "- Ana bağlantılar 30×20×2 mm alüminyum dikdörtgen boru ve 2700 kg/m³ yoğunlukla modellenmiştir (`ESTIMATE`).",
            "- Bilek aktarma kütlesi `0.12 kg`, gripper `0.22 kg`, hedef yük `0.10 kg` kabul edilmiştir (`ESTIMATE / UNVERIFIED`).",
            "- J2 yerçekimi torku tüm bağlantılar yatay ve yük en uzakta iken hesaplanmıştır (`CALCULATED`).",
            "- İvme torku noktasal/ince bağlantı atalet yaklaşımı ve CAD J2 maksimum ivmesiyle hesaplanmıştır (`CALCULATED ESTIMATE`).",
            "- Tablodaki toplam torkta güvenlik katsayısı, kayış kaybı, sürtünme veya motor tork-hız düşümü yoktur; motor seçimi için doğrudan kullanılamaz.",
            "- Çevrim süresi kübik joint-space profil, CAD joint hız/ivme limitleri ve basit çarpışma proxy'leriyle elde edilmiştir (`SIMULATED`).",
            "",
            "## 3B erişilebilirlik haritası",
            "",
            f"CAD taban geometrisi için joint-limit ızgarasından `{point_count}` zemin-üstü nokta üretildi. `simulation/results/reachability_map.ply` MeshLab/CloudCompare ile üç boyutlu açılabilir; aynı verinin CSV biçimi `simulation/results/reachability_map.csv` dosyasındadır.",
            "",
            "## Doğrulama kapısı",
            "",
            "Kol boyu dondurulmadan önce gerçek kamera kalibrasyonu, CAD mesh interference kontrolü, motor/redüksiyon tork-hız eğrisi, bağlantı esnemesi ve en az 100 fiziksel pick hedefi doğrulanmalıdır. Hiçbir varyant `PHYSICALLY VERIFIED` değildir.",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = _evaluate()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULTS_DIR / "geometry_variant_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    point_count = _write_point_cloud(ArmKinematics())
    _write_report(rows, point_count)
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote simulation/results geometry CSV and {point_count}-point reachability map")
    for row in rows:
        cycle_text = "N/A" if row["mean_cycle_s"] is None else f"{row['mean_cycle_s']:.3f}s"
        print(f"{row['variant']}: {row['success']}/100, {cycle_text}")


if __name__ == "__main__":
    main()

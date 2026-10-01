# Purchasing notes — checked 2026-08-20

No order has been placed or authorized.

`CONTROLLED_COMPONENTS.csv` is the authoritative V0 baseline. `PURCHASE_CANDIDATES.csv`
is retained only as the earlier alternative study and must not override controlled
manufacturer part numbers.

## Decision gates

- **Motors:** controlled geared-motor part numbers may be quoted, but purchase/release requires regenerated CAD mass properties, manufacturer torque-speed curves, J2 counterbalance review and a one-axis bench test plan.
- **Safety chain:** do not purchase from the candidate list as a set. A machinery-safety engineer must approve the complete architecture, including final switching devices and gravity-drop mitigation.
- **AI computer:** benchmark the intended detection model on an existing PC first. Buy an embedded computer only after latency, power, and software compatibility data exist.
- **Camera:** Camera Module 3 Wide is the low-cost V0 preference only for a controlled, approximately planar test surface with camera-to-table calibration. Use RGB-D only if measured height variation breaks the planar solution.
- **Battery/V1:** no battery candidate is selected. V1 is manually pushed; capacity, chemistry, BMS, charger, environmental enclosure, and transport requirements remain open.
- **Traction/V2:** no traction components should be bought before V0 and manual-push V1 pass their gates.

## Price interpretation

### Recorded purchases updated 2026-09-09

The latest actual-purchase ledger is [FIGBOT purchase tracker V6](../outputs/purchase_update_20260909/FIGBOT_SATIN_ALMA_MALIYET_TAKIBI_V6.xlsx). It preserves all 44 original transaction rows and the 21 product rows added in V5 (1,735.61 TRY), then adds the Fideco 150 mm digital caliper (252.00 TRY). Recorded cost is now 8,774.90 TRY; new shipping/final order payment are TBD. See ASM-082/083 for screenshot price, quantity and VAT assumptions. The candidate-price guidance below concerns researched parts, not this actual-purchase ledger.

Prices are single-unit web prices in the shown currency, checked on 2026-08-20. They exclude VAT, Turkish import duties, shipping, cables not explicitly bundled, exchange-rate changes, and distributor lead-time risk. Blank price means `QUOTE_REQUIRED` or `PURCHASE_RESEARCH_REQUIRED`; it does not mean zero.

NVIDIA's current marketplace and FAQ show $399 for the Jetson Orin Nano Super Developer Kit while some official marketing pages still show $249. The candidate table therefore uses the current marketplace price and records the conflict.

## Motor caveat

Stepper holding torque is not available torque at speed. The controlled baseline uses 10:1 planetary gearboxes on J1-J4 with derated J2 speed/acceleration. Vendor torque-speed curves at the intended 24 V bus and current settings are mandatory inputs; J2's 7.11 N m calculated peak exceeds the selected gearbox's 6 N m permissible rating and therefore requires counterbalance/duty validation.

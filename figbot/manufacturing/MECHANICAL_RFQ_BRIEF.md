# FIGBOT mechanical design-freeze and production RFQ brief

Revision: `RFQ-RC1`  
Status: **RFQ DESIGN INPUT — NOT A PRODUCTION RELEASE**  
Units: millimetres unless stated otherwise

## 1. Purpose

This package requests a staged commercial and technical proposal for the
mechanical completion of a modular mobile robot. It contains the current
parametric CAD, custom-arm manufacturing candidates, vehicle packaging model,
interface controls and validation gates. Software, perception algorithms and
user-interface development are outside the requested scope.

This is a preliminary **V1 demonstration and feasibility design**, not a frozen
series product. Its operational purpose is to use a camera to locate objects on
the ground, collect them with the arm and place them in the onboard basket. The
maximum handled-object mass is 100 g, so the arm should be lightweight, fast and
economical; unnecessary lifting capacity is not required. The 100 g is object
mass only; gripper/arm mass, acceleration and appropriate engineering margins
must also be included in sizing.

The requested system performance objective is **50-100 successfully collected
objects per minute within a 5 m2 test area** (3000-6000/hour equivalent). This
supersedes the previous 300/hour proposal. It is an ambitious, UNVERIFIED target,
not a performance claim for the current CAD. Sequential picking would require
0.6-1.2 seconds per object. Please assess feasibility, state the achievable V1
demo rate and propose an alternative architecture if necessary. The 5 m2 area
does not mean instantaneous arm reach; base repositioning may be needed. System
tests must include perception, gripping, basket deposit, retries and required
base repositioning. Object spacing, test duration and replenishment are TBD;
hourly equivalent is not a demonstrated sustained hourly capacity.

If the demonstration succeeds, the commercial opportunity may expand to
hundreds of units. This statement is a potential future volume for quotation
planning and does not authorize or guarantee a series order.

The supplied PDFs are simplified reference drawings with envelopes and critical
notes. They are not fully dimensioned production drawings; completion of hole
patterns, datums, tolerances, retention details and inspection dimensions is an
explicit Phase A deliverable.

The supplier shall not manufacture a series batch directly from the vehicle
packaging assembly. The required sequence is:

1. design review, purchased-component selection and design freeze;
2. detailed drawings, tolerances, DFM and first-article manufacture;
3. physical validation and correction of the first article;
4. controlled production release and unit pricing for series quantities.

## 2. Controlled architecture

| Item | RFQ baseline | Release state |
|---|---|---|
| Structural frame | 600 x 450 mm bolt-together frame | Digital packaging baseline |
| Running gear | Four nominal 254 x 60 mm pneumatic wheels | Supplier/sample dimension gate |
| Traction | Two independently driven rear wheels | Motor output interface gate |
| Steering | Front Ackermann, maximum +/-30 degrees | Knuckle/actuator design-freeze gate |
| Wheelbase / track | 430 / 670 mm | Calculated packaging baseline |
| Payload design target | 20 kg | Physical validation required |
| Custom arm | Four axes plus gripper, 605 mm nominal tool-tip reach | Engineering candidate / first article required |
| Maximum handled object | 100 g | V1 physical payload test required |
| Requested throughput / test area | 50-100 objects/minute within 5 m2 | Feasibility UNVERIFIED; supplier assessment and timed system test required |
| Arm installation | Removable front-centre mounting interface | Final adapter and stability review required |
| Battery | Low central removable tray | Final SKU, mass and terminal gate |
| Electronics | Serviceable removable tray | Mechanical envelopes only |
| Sensor support | Braced bridge for forward/downward-facing sensors | Vibration validation required |

The rover assembly currently contains official purchased-arm geometry as a
packaging reference. The requested mechanical scope uses the separate 605 mm
custom-arm assembly. The supplier shall quote the adapter and vehicle
integration of the custom arm. A purchased arm may be returned as a separately
priced cost-reduction alternative, but must not silently replace the requested
custom-arm scope.

## 3. Supplier scope

### Phase A — design freeze and DFM

- Review the supplied STEP assemblies and numbered custom-part files.
- Select or confirm wheels, hubs, bearings, steering knuckles, tie rods,
  actuator, rear gearmotors, shafts, sprockets, chain, battery and fasteners.
- Replace every envelope/TBD interface with controlled supplier CAD or a signed
  incoming-inspection drawing.
- Complete the Ackermann geometry, steering stops, bearing arrangements,
  motor/gearbox mounts, arm adapter, guards, cable routes and service access.
- Perform structural, stability, full-sweep interference and tolerance-stack
  reviews for the stated target.
- Return editable native CAD, neutral STEP, detailed drawings, BOM and the
  resolved interface register.
- Ensure that any supplied controller, driver, compute or sensor hardware can be
  reprogrammed after delivery by our team. Provide documented pinouts,
  communication protocols, API/SDK information and firmware-loading access; do
  not use a vendor-locked control architecture.

### Phase B — first article

- Procure standard components and manufacture all agreed custom parts.
- Provide dimensional first-article inspection records for controlled
  interfaces.
- Assemble one complete mechanical prototype.
- Perform the tests in `PRODUCTION_VALIDATION_MATRIX.csv` that are within the
  supplier's capability and record raw results.
- Correct the design and drawings for issues found during assembly/testing.

### Phase C — production proposal

- Deliver the controlled production CAD/drawing/BOM release after first-article
  acceptance.
- Quote unit prices for 1, 10, 50 and 100 units.
- Separate non-recurring engineering, tooling, purchased parts, custom parts,
  assembly, inspection, packaging and freight.
- State minimum order quantity, lead time, payment terms, warranty, spare-part
  support and Incoterms.

## 4. Required commercial response

The quotation shall identify:

- company legal name and manufacturing location;
- named technical and commercial contacts;
- Phase A, B and C price and lead time;
- assumptions, exclusions and proposed deviations;
- make/buy split and proposed manufacturer part numbers;
- ownership and delivery rights for native CAD, drawings and tooling;
- prototype correction/revision allowance;
- first-article inspection scope;
- production quality system and traceability method;
- export packing and estimated shipping to Turkiye.

## 5. Release boundaries

The supplied files are suitable for quotation, engineering review and
first-article planning. They are not evidence of verified load capacity,
stability, braking, steering durability, fatigue life or safe unattended use.
No series production may be released until the interface register is closed,
the first article is measured and the applicable physical validation records
are accepted.

Requester: Hayen Bilişim Teknolojileri Ve Enerji Çözümleri Ltd Şti.
Technical and commercial contact: Sinan Ekiz, Computer Engineer / Project Manager.
Website: hayenteknoloji.com. Official contact email: sinan.ekiz@hayenteknoloji.com.

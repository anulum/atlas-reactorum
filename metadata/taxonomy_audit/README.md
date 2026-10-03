<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — taxonomy audit and citation data contracts
-->

# Taxonomy audit and claim citations

The maintained `audit.tsv` contains classification and source-scope triage for
all 135 taxonomy entries. Its dates and statements remain historical records.
The original `build_audit.py` reproduces the first 123-entry snapshot; it does
not overwrite the later maintained audit rows or complete scientific review.

`claim_citations.json` adds 599 source-inspected statements for 135 entries from
148 sources. Each statement has a section, a support boundary and an inspection
date. PDF citations distinguish one-based file pages from printed page labels;
HTML and XML citations identify a heading or section. These partial observations
include 480 statements bound to 405 distinct physical fields: PWR, BWR and
integral PWR principles, strengths and challenges, plus the
principle, strength and challenge of six HTGR/fast-reactor types, SCWR, VHTR and three salt-based types, two heavy-water types and Magnox, AGR and RBMK, plus seven research configurations, four electrolysers and five fuel-cell types. They do not
verify all fields or the complete maturity and evidence classification of an entry.
The five batch, semi-batch, CSTR, plug-flow and CSTR-cascade entries add 25
statements across their 15 physical fields. Ideal mixing and plug flow are model
assumptions; real vessels may have bypassing, dead zones or axial dispersion.
Heat-release and multiple-state concerns are conditional on exothermic reactions
and operating conditions. Kinetics determine conversion and selectivity benefits.
Complete entry review remains pending for all 135.

The membrane, microchannel and segmented-flow entries add 13 statements for
nine physical fields and the segmented-flow classification. Segmentation is
a flow configuration rather than a mandatory microchannel subtype: the
2026 Gatti et al. experiment uses a 3 mm tube. The historical audit warning is
preserved, while the native entry and TSV now use no architectural parent.
A membrane reactor may hold its catalyst separately from the selective
membrane. Heat and mass transport depend on mixing geometry. Phase separation
and parallel-channel flow control have separate supporting experiments; the
photochemical numbering-up case does not validate parallel segmented flow.

The inspected MDPI book contains the 2018 Caravella et al. article on printed
pages 115-116 (PDF pages 126-127); article CC BY and whole-book CC BY-NC-ND
notices differ. The Sato et al. 2024 review corrects the original catalogue's
Jensen attribution; the earlier Recaptcha capture remains distinct from the
new verified-TLS full article. Gas-slug and parallel photomicroreactor papers
have noncommercial publisher notices. The latter was published in November
2017 and appeared in the January 2018 issue. The 2026 segmented-flow paper
demonstrates an NVP-precursor process, not universal ideal plug flow or
commercial acceptance. No source original or figure is redistributed.


Eight catalytic/multiphase entries add 31 statements across 24 physical fields.
High packed-bed catalyst loading is qualified to slow reactions without dominant
transport limits. Solids recirculation enables repeated contact; it does not
establish universally high throughput. The basic bubble-column configuration
uses gas-driven mixing, and airlift shear increases with aeration. Those eight
entries retain their kinds, maturity and evidence classifications.

The new originals include preliminary MIT notes, manufacturer descriptions,
NETL conceptual models, bench-scale sorbent tests, course materials, actual
column/airlift experiments and institutional abstracts. Model uniformity,
conceptual separators and fitted correlations are not operating-plant acceptance.
Purdue bibliographic metadata dates the dissertation 2015, separately from its
2016 online deposit. The 2017 NETL moving-bed cover date differs from the 2018
report identifier. QUB supports high catalyst loading through its 2016 chapter
abstract; the full chapter was not inspected. The Pittsburgh source is its 1997
dissertation abstract. The bubble-column source is the October 2022 arXiv v2
preprint, with no claim of journal acceptance.

The scanned Fogler slurry chapter was checked using rendered pages and
derivative OCR; PDF page 2 is printed 597. The DTU 2012 thesis
chapter-opening PDF page 94 has no printed numeral. Relevant sections were
inspected, not every page of the thesis or other lengthy originals. Dates of
the Fogler and NPTEL materials are unknown. Original rights notices remain
separate: MIT CC BY-NC-SA, UOP reserved rights, DTU private-study terms and
the 2021 airlift article’s CC BY notice are not replaced by the metadata licence.
No source figure, original PDF, HTML, XML or OCR derivative is embedded in the
presentation.

The registry contains source URLs, titles, capture provenance and original-byte
SHA-256 hashes. One hundred and fourteen sources retain their verified publisher-TLS retrieval timestamps.
Twenty-three were inspected from retained owner-controlled copies whose hashes match
the prior custody manifest. Their original retrieval dates are unknown, so
`captured_at` is null. Inspection does not claim a fresh download or
publisher access check for those retained originals. The IAEA HTGR report is dated February
2001 on its cover and the fast-reactor report is dated 2012 in its publication
notice. Their programme descriptions and planned tests are historical, including
the conventional ALLEGRO start-up fuel and later refractory-fuel design target.
Source-inspected coolant properties are distinct from current plant performance.
The full R-100 course carries 14 June
2017 page footers; the BWR chapter carries footer code 0400. Neither is treated
as independent verification of its publication year. Originals are
catalogue-only and are not redistributed. The
licence for authored citation metadata does not grant rights to publisher PDFs,
HTML, illustrations or other original material. Hashes identify the inspected
version; a later online document may differ. Inspection dates are not publication
dates. The archived EPA glossary is a historical terminology source.

The MIT Spring 2007 notes are preliminary course materials. Their first page
is unnumbered; citations say so rather than inventing a printed label. The
notes' CC BY-NC-SA terms remain separate from the authored metadata licence.
HSG143 was first published in 2000 and reprinted in 2008; its PDF reproduction
notice is not replaced by a general website licence. INDG254 is the seven-page
leaflet dated 08/14. This UK guidance does not certify a particular process.
Stopping a semi-batch feed can leave accumulated reactants still reacting.

Cascade sources describe physical reactors in series. The author-hosted 2007
abstract supports nonlinear coupling without accepting full-paper equations or
numerical benefits. The 2015 coauthor-institution abstract describes step-feed
operation and finds no advantage over a single reactor for its stated Monod
model without recycle. IMA's hosted 2019 case study reports separate reaction
stage temperatures and burst interstage transfer; the original Hu et al. journal
paper was first published on 3 July 2018, as recorded by RSC. This case study
does not demonstrate fresh feed into every stage, uniform continuous transfer,
universal performance or FDA endorsement. These sources jointly support the
configuration options while retaining their distinct limits. Buffalo's 2014
network notes support connected balances and the economic choice of stage count.


Two GIF technology pages were retrieved over verified publisher TLS on
1 October 2026 and privately retained with exact byte hashes. Their publication
dates are unknown. SCWR cycle efficiency is a design potential, and VHTR
industrial heat remains an application potential requiring plant-specific
coupling and qualification. GIF uses VHTR broadly, including lower-temperature
HTGR examples; the higher-temperature target does not establish a fixed outlet
temperature or the deployment of every design. Numerical table inconsistencies
and historical fleet totals on those pages are not accepted by these citations.

The retained IAEA salt reports date from May 2013 and November 2023. Thermal
liquid-fuel concepts can use graphite or other moderators, and fuel circulation
is not universal. Fast liquid-fuel concepts include homogeneous and heterogeneous
families; fuel-cycle flexibility remains design potential. Fluoride-salt cooling
of solid fuel is distinct from dissolved-fuel salt. Salt chemistry, qualified
components and decay-heat removal require design-specific evidence; none of
these statements grants whole-entry or current deployment approval.

The heavy-water report is the publisher Part 1 file of the April 2002 TRS 407
report. CANDU pressure tubes differ from the small-pressure-difference internal
channels of pressure-vessel designs. Reported Atucha internal-tube hydriding
and heavy-water recovery are bounded material and management concerns.
Magnox citations document historical operation, dismantling and reactive
cladding waste. The September 1998 gas-reactor report title follows its actual
title page; scanned printed page labels do not follow a fixed PDF offset.
The IAEA graphite history explains AGR fuel/cladding and improved steam
conditions, with no numerical performance claim. ONR supplies design-specific
graphite ageing, inspection and safety-case requirements; its inclusion of
Sizewell B in a generating fleet list does not make that PWR graphite moderated.
The November 1992 INSAG-7 analysis describes historical RBMK feedback and
channel-integrity problems, not present-day coefficients or certification.
Original publication dates of the two HTML sources are unknown; the ONR page
shows an update date, separately from the known retrieval date.

The research-configuration citations distinguish open-pool access, closed-tank
boundaries and design-specific tank-in-pool separation. The latter combines
geometries; a sealed core, storage purpose and direct core access are not universal.
The aqueous report is dated September 2008 and documents dissolved fuel,
isotope-production development, radiolysis, chemistry and retention concerns.
Homogeneous composition does not imply uniform gas or neutron distributions or
accept blanket economic and safety projections. The training module states a
2015 update in its preamble; its plant examples and classifications are historical.
The research reliability report is dated May 2023 and the subcritical report
September 2021. Multiplication below criticality needs an external source, but
source control alone does not establish design safety. EPFL CROCUS and its
course supply named physics, teaching, control and licensing examples. Mainz
supplies a named pulse-mode example, with a separately stated 31 July 2023 update.
Their original publication dates are unknown. Neither named example establishes
universal facility specifications, jurisdictional licensing or pulse capability.

The electrochemical citations separate water-splitting electrodes from fuel-cell
fuel oxidation and oxygen reduction. The November 2004 NETL handbook supplies
historical reaction, electrolyte, water-management, fuel-purity, acid-reservoir,
carbon-dioxide and thermal-stress descriptions. Its fleet counts, comparisons
and life goals do not establish current operation or universal specifications.
The December 2024 DOE assessment is independently dated by the publisher's
technical-publications index. Material, gas-separation, dynamic-operation and
stack-life requirements are distinct from future cost and durability targets.
AEM reduced precious-metal dependence remains a development potential.
Solid-oxide thermal integration can reduce electrical demand while still
requiring heat; it is not an unconditional primary-energy or emissions benefit.
PNNL-29240 has October 2019 title pages; its publisher page's July 2024 date is
separate. Its ceramic button-cell study supports steam and carbon-dioxide
electrolysis, including co-electrolysis, without commercial-scale acceptance.
All three originals were retrieved over verified publisher TLS and remain
privately retained. No original document is embedded in the offline presentation.

The four culture entries add 16 statements across 12 physical fields. Stirred
vessels combine impeller agitation with monitoring; oxygen transfer, cell-specific
shear and sterile handling have separate supporting sources. Mixing is not
universally homogeneous. Fed-batch feeding can limit substrate overload under
process-specific kinetics, while culture volume changes. Chemostat steady state
requires an appropriate dilution rate and measured establishment; population
constancy does not imply identical single cells. Washout and contamination remain
separate concerns. Perfusion can support high density with effective cell retention
and adequate supply. Filter fouling differs from the flow and concentration limits
of membrane-free inertial retention.

MIT lecture 13 uses the existing verified-TLS original and its actual earlier
retrieval timestamp. Lecture 19 matches retained private custody; its retrieval
date stays unknown. Their first pages have no printed numeral. The stem-cell
review is dated 17 May 2021, the CHO experiment 27 July 2017 and the chemostat
protocol 14 October 2013. The gut-community protocol was published 31 October
2024 and has a 20 December collection date. Only relevant sections were inspected.
The 350 mL CHO experiment does not establish commercial scale or universal recovery.
MIT CC BY-NC-SA, article CC BY, the JoVE copyright notice and gut-protocol
CC BY-NC-ND terms remain distinct; originals and figures are not redistributed.
The existing scale-up perspective has corrected Delvigne/Noorman authorship,
but is not evidence for all four culture modes. All full-entry reviews remain pending.

The three photochemical entries add 11 statements across nine physical fields.
The homogeneous entry uses the actual dissolved-methylene-blue flow experiment,
with the photosensitiser distinguished from the dye in its light collector.
Short optical paths aid illumination; light alone does not guarantee selectivity.
Numbering-up must balance flow distribution, light-harvesting area, reabsorption
and pressure loss. The model reaction does not establish industrial throughput.

The retained 2019 photocatalytic review has four authors: Visan, van Ommen,
Kreutzer and Lammertink. It was published on 20 March 2019; its nine PDF pages
carry printed pages 5349-5357. The catalogue's two-author attribution is corrected,
while original custody metadata stays historical. The retrieval date is unknown.
Dispersed catalyst can provide short diffusion distances, with aggregation,
scattering and a later separation step as distinct concerns. A fixed coating
avoids slurry-particle separation, but that does not prove its lifetime or absence
of leaching. Layer illumination and internal and external transport remain
coupled design constraints. Relevant sections were inspected without adopting
universal optical-thickness limits or idealised kinetic laws. Both source
originals have noncommercial/no-derivatives notices and remain private.
All three kinds, maturity and evidence labels remain unchanged; whole-entry
review and independent scientific acceptance remain pending.

Four plasma entries add 15 statements across 12 physical fields. A dielectric
barrier controls the discharge; its geometry does not guarantee uniformity or
high process efficiency. Microwave excitation can avoid discharge electrodes,
but coupling, reflected power, cooling and vacuum loads remain distinct concerns.
Gas-flow-driven arc extension is supported by an actual air-jet experiment;
shortcuts and rupture prevent a universal monotonic relation between flow and
arc length. Warm gliding-arc operation differs from fully thermal operation.
Electrode wear and reaction recombination depend on the regime and process.

The thermal-arc reference reports bench-scale ash smelting separately from
vaporisation modelling and preliminary pilot design. It supports high-temperature
material conversion and power/refractory thermal requirements, without proving
refractory lifetime or commercial operation. The retained 2023 Engineering
Journal article concerns hydrogenation of vegetable oils and biodiesel, with
five authors; its earlier wastewater title is corrected in the catalogue.
Its original retrieval date remains unknown. The Miao review's title and five
authors are corrected from publisher-deposited metadata; its full text was not
inspected and does not support these physical claims. Six inspected sources
supply the claims, with source-specific notices retained and no original or
figure redistributed. All four kinds, maturity and evidence labels remain
unchanged; full entry review and independent acceptance remain pending.

Four polymerisation entries add 19 statements: four preparation-method
classifications and 15 statements across their 12 physical fields. Bulk,
solution, suspension and emulsion describe preparation methods rather than
exclusive vessel geometries. Bulk viscosity and heat removal depend on
conversion and chemistry. Solution dilution can aid heat transfer; solvent
recovery is required where the product or application needs solvent removal.
Suspension droplet stability and polymer accumulation in stagnant regions
are distinct concerns; a blanket ban on continuous operation is not adopted.

The tutorial review distinguishes initiation within suspension droplets from
conventional emulsion growth outside the large monomer-reservoir droplets.
Miniemulsion and step-growth systems have separate mechanisms. High emulsion
rates are a potential under suitable compartmentalisation and termination
kinetics. Low bulk viscosity is also conditional: the PVAc/PVA experiment
reports gelation and temperature excursions. Its optical monitoring does not
independently establish complete monomer conversion. Particle-size control
and residual monomer or formulation ingredients require process-specific
evidence.

NPTEL publication dates are unknown; their broad claims about particle size,
agitation and physical properties are excluded. The Elbert review was published
in July 2010, before its January 2011 issue and later manuscript availability.
The 2021 experimental article retains all five authors. Five used source
originals remain private with exact capture timestamps and hashes. The article
CC BY notice, manuscript copyright and course notices remain distinct; no
original or figure is redistributed. All kinds, maturity and evidence labels
are preserved. Full entry review and independent acceptance remain pending.

Five thermochemical entries add 20 statements: one fast-pyrolysis process
classification and 19 statements across 15 physical fields. Moving or fixed
beds have drying, pyrolysis and gasification zones whose order depends on the
configuration. Coarse-feed compatibility does not remove fines, caking or tar
constraints. Fluidised beds use back-mixing to approach temperature uniformity;
feed preparation, ash agglomeration and solids separation remain important.

Entrained-flow designs can accept fine particles or atomised liquid/slurry
feed. High conversion and low tar are conditional potentials, rather than
universal numerical performance. Feed preparation and slag handling depend on
the feed system. The handbook's terminal-settling-velocity explanation is not
adopted as a minimum-fluidisation criterion.

Fast pyrolysis uses rapid heating without added oxygen and can use different
reactor geometries. Liquid-product potential depends on vapour collection;
rapid cooling limits secondary reactions, while stored bio-oil can change
viscosity and phase stability. A particular laboratory's cryogenic apparatus
does not prescribe industrial equipment. Supercritical-water gasification can
avoid preliminary feed drying but still needs heating, pressure control,
suitable materials and management of salt or char accumulation.

The NETL handbook is dated July 2022 despite its current 2026-02 hosting path.
The NREL process brochure is dated January 2009, correcting the earlier 2008
catalogue date; its current official document URL is recorded. The bio-oil
ageing procedure was issued in October 2021. The retained SCWG manuscript
identifies Brian R. Pinkard and six coauthors, correcting the shortened
attribution without rewriting historical custody. Its retrieval date remains
unknown. Seven used originals stay private; article public-domain notices,
method permissions and third-party figure rights remain separate. All kinds,
maturity and evidence labels remain unchanged; complete reviews are pending.

The chemical-looping and sequencing-batch entries add seven statements:
one activated-sludge operating classification and six statements across their
six physical fields. NETL describes a solid oxygen carrier cycling between
fuel and air reactors. Their separate gas streams can simplify downstream
capture, but no guaranteed purity, capture efficiency or energy saving is
adopted. Carrier durability, solids circulation and scale-up remain development
concerns; the overview does not prove commercial system readiness.

The EPA fact sheet describes fill, react, settle, draw and idle phases in a
conventional sequencing batch reactor. A complete plant can use multiple
basins and external pretreatment or equalisation. The continuous-inflow ICEAS
variant is distinguished from the conventional batch configuration. Timing,
control-system maintenance and influent characteristics require site-specific
design. Historical manufacturer guarantees, costs and largest-plant claims
are not adopted as current universal values.

The EPA title is dated September 1999 despite its 2022-10 hosting path and PDF
creation metadata. Its pages are unnumbered and locators explicitly say so.
NETL's publication date is unknown. The sources remain private, including
third-party figures and tables whose rights are not assumed from agency
hosting. Existing source partitioning is preserved; all kinds, maturity,
evidence and complete-review boundaries remain unchanged.

The five anaerobic digestion types add fifteen physical-field statements
while preserving their existing classification citations. AgSTAR distinguishes
mixed tanks, elongated manure-slurry vessels, covered lagoons and attached
biofilm media. Mixing promotes uniformity rather than guaranteeing a perfectly
uniform vessel. Plug-flow feed suitability is limited to relatively high-solids
manure slurry; accumulated solids can require clean-out. Lagoon simplicity
and gas production depend on volume, land and ambient climate. Fixed-film
compactness depends on feed solids and design; influent solids can obstruct
media and require separation.

The Mainardis, Buttazzoni and Goi review describes conventional UASB flow
through retained granular biomass without requiring carrier media. Granulation,
hydrodynamics and effluent post-treatment remain wastewater-specific concerns.
The review does not establish a new Atlas plant experiment, universal removal
efficiency, energy recovery or discharge safety.

AgSTAR's project handbook is the April 2020 third edition, despite its
2014-12 hosting path. The operator guidebook is dated November 2020 and names
David Palmer and Phil Lusk as primary authors. Their retained original retrieval
dates remain unknown. The UASB article was published on 10 May 2020; its
author CC BY 4.0 notice and bibliographic record were inspected. Selected
original pages and sections support these fields; no complete handbook review
or independent entry approval is claimed. Third-party figures are not
redistributed. No numerical solids, cost or performance value is adopted as
a universal design requirement.

The remaining five physical fields of PWR, integral PWR and BWR add eight
citations. The 2025 IAEA PRIS publication supports qualitative PWR operating
experience through a type-labelled fleet and older commercial-operation
examples. Its tables describe 31 December 2024, with submissions through
20 June 2025; they are not live fleet statistics. The cumulative experience
of all reactor types is not assigned to PWR.

PWR challenges now name high-pressure boundary integrity and spent-fuel
handling. The NRC course supports pressurisation, shielding during fuel
movement and continuing decay-heat removal. Historical storage periods,
fleet counts and regulatory descriptions are not current operating guidance.

Integral layouts reduce external primary-circuit piping. This does not imply
a universally smaller plant, lower cost or elimination of every pipe break.
The November 2025 NEXSHARE working paper identifies integral-system inspection
and maintenance challenges, and validation uncertainties for natural-circulation
designs. Natural circulation is a design-specific mechanism. The IAEA training
course explains scaling, experimental validation and weak driving forces;
neither educational simulators nor the working paper qualify a plant.

BWR core vapour can introduce flow and reactivity-feedback challenges.
NRC's nitrogen-16 discussion supports shielding concerns in the main steam
circuit. Neither observation establishes instability or a dose exceedance
at every plant. Third-party tables and figures remain private. Complete
entry review and maturity/evidence acceptance remain pending.

Three breed-and-burn concepts add thirteen citations: three naming
observations and ten statements across nine physical fields. Gilleland,
Petroski and Weaver's 2016 article describes in-core breeding and consumption,
potential fuel utilisation and the coupled reactivity/materials problem.
All three authors worked for TerraPower. Benefits and qualification targets
are attributed development analysis, not independently demonstrated plant
performance. The paper's proposed 2026 deployment date is not current status.

The traveling-wave mechanism concerns motion relative to fuel. A standing-wave
variant moves fuel while keeping the reaction region approximately stationary.
Its potential cooling-layout benefit replaces an unsupported general claim
of better fuel control. High-burnup qualification and fuel-handling equipment
remain development requirements.

IAEA-TECDOC-1691 describes CANDLE's proposed axial-wave configuration with
fixed solid fuel. Its ideal equilibrium assumptions do not establish a
TerraPower result or eliminate controls from every implementation.

The genuine complete publisher HTML supplies heading locators; no file-page
numbers are invented from its journal pagination. The retained IAEA source
keeps its unknown retrieval timestamp. No original figures or tables are
redistributed, and no precise article reuse licence is inferred from an
open-access label. Numeric utilisation, risk, waste and cost projections,
heavy-ion samples and fabrication tests are not adopted as integrated
reactor qualification. All complete-entry reviews remain pending.

Tokamak, spherical-tokamak and reversed-field-pinch entries add thirteen
citations across naming and nine physical fields. Fusion Physics describes
external toroidal coils and plasma-current poloidal fields, tokamak research
experience, disruptions, spherical-tokamak geometry and pressure limits,
and RFP field reversal and relaxation-driven transport. Its verified full-book
title replaces the earlier chapter-oriented catalogue label.

Fundamentals of Magnetic Fusion Technology supplies tokamak power-exhaust
and steady-state current-drive requirements. Dated ITER schedules and example
heat loads are not current operating results or universal design values.

For the spherical tokamak, high beta means pressure relative to magnetic
pressure. The book's transient experimental results and stability conditions
do not establish a universal steady-state performance advantage. Wilson and
coauthors' STPP paper supplies a low-aspect-ratio centre-rod example and
space/shielding constraints in fusion-power design. Its modeled power,
efficiency, component lifetime and costs remain projections. The paper
belongs to the 2002 conference; its official proceedings carry a 2003 footer.

RFP applied-field advantages remain relative and potential engineering
benefits remain conditional. Magnetic relaxation and stochastic-field transport
are linked concerns; the book also describes improved-confinement techniques.
An RFP is distinct from a field-reversed configuration.

Both retained books keep unknown retrieval timestamps. Complete selected
book pages and the complete eight-page conference paper were inspected.
IAEA copyright notices and proceedings editorial limits do not grant blanket
redistribution. Originals, extracts, figures and tables remain private;
all complete-entry reviews and maturity/evidence fields remain pending.

Stellarator, heliotron/torsatron and optimised modular stellarator entries add
seventeen citations: three naming observations, eleven physical statements
across nine fields and three bounded historical-operation observations.
Fusion Physics describes externally generated three-dimensional fields,
continuous helical windings and discrete shaped modular coils. External fields
offer sustained-operation potential; bootstrap/pressure currents can still exist,
and exhaust, transport and components constrain actual operation.

The technology book supplies LHD-specific coil/transport engineering and
stellarator power-design requirements for coil accuracy, divertors, blankets
and maintenance. Its numerical tolerances and reactor studies are design-specific
requirements or projections, not achieved integrated power-plant performance.

Beidler and coauthors' corrected 2021 W7-X article supports a narrower strength:
optimisation can reduce neoclassical transport losses. Measured plasma profiles
and VMEC/DKES calculations support the authors' configuration-specific assessment.
Rescaled LHD counterfactuals use common field/volume; they are not a direct
head-to-head experimental ranking. Turbulent transport remains significant,
the studied high-performance phase is transient, and diagnostic uncertainty
is described in Methods. No universal reduction of all loss channels is asserted.

Historical observations separately identify W7-A currentless operation in 1980,
LHD's reported 54-minute low-power/low-density discharges by 2009, and W7-X's
2015 start and 2017/2018 experiments. LHD parameter maxima come from different
discharges; duration and high-performance records are not combined. These
observations do not close maturity/evidence fields or establish current operation.

The W7-X paper and Publisher Correction were inspected in full. The correction
changes curve-letter references and a team member's name; its erroneous 2011
original-publication date is rejected against the original article's 2021 date.
Both publisher CC BY 4.0 notices retain third-party exceptions; deposited-copy
cover notices were also inspected. IAEA copyrights remain separate.
Originals, extracts, figures and tables remain private. Both retained books keep
unknown retrieval timestamps, and all complete-entry reviews remain pending.

Magnetic mirror, tandem mirror and gas-dynamic mirror entries add fifteen
citations: three naming observations, nine physical statements across nine
fields and three bounded historical-operation observations. The retained
Fusion Physics book is already registered; no new source object, catalogue
row or retrieval timestamp is introduced.

Mirror reflection relies on adiabatic magnetic-moment conservation and suitable
pitch angle. Loss-cone particles escape through the ends; collisions replenish
those losses, and electron energy losses remain a concern. The straight central
solenoid and end-tank access describe geometry, not universal simple coil
construction, operating economics or direct-conversion efficiency.
The generic fusion-grade parameter table is an assumed example.

Tandem end cells can establish electrostatic potential barriers for central-cell
ions. TMX demonstrated this mechanism; thermal barriers require additional
control and heating, and MHD stabilization can complicate field geometry and
transport. Projected gain or theoretical central-cell scaling is not a measured
net-energy result or integrated reactor qualification.

The gas-dynamic condition compares effective loss-cone scattering mean free
path with trap length. Collisional background outflow can coexist with injected
fast sloshing ions; not all populations have the same collisional regime.
Neutral-beam heating and axial outflow remain requirements and losses.
The book describes GDT stability experiments and proposes larger volumetric
neutron sources for materials testing. Proposed output or actinide-burning
applications are not deployed-source or power-plant results.

The historical observations identify 2XIIB instability suppression, TMX
ambipolar confinement and GDT experiments. They do not close typed maturity
or evidence fields, establish current operation, or guarantee stability for
every mirror configuration. Complete selected book pages1031–1044 were read;
pages1042–1043 were rendered and visually inspected. The original book's
unknown retrieval timestamp remains null. Protected originals and figures stay
private; all complete-entry reviews remain pending.

Magnetic cusp and levitated dipole entries add ten citations: two naming
observations, seven physical statements across six fields and one bounded
laboratory-history observation. The retained Fusion Physics source and catalogue
row remain unchanged; one genuine author final report is added.

The cusp's favorable local curvature is a conditional MHD property. The same
source describes loss of magnetic-moment conservation near the field null,
point/ring-cusp particle escape and instability after central plasma empties.
This is not universal stable confinement; proposed electrostatic plugging
and Polywell configurations require separate evidence.

Dipole levitation produces closed laboratory field surfaces around a current
ring. Earth's magnetosphere has different atmospheric end boundaries.
The strength now names inward particle redistribution and improved hot-electron
stability in studied discharges rather than unspecified transport advantages.
Kesner and Mauel's complete 2013 LDX final report documents supported-versus-
levitated density measurements, limited four-channel profile inversion and
heating/fueling-dependent instability margins. Centrally peaked density does
not itself prove a longer particle lifetime, and instability bursts can occur.

Challenges retain internal-coil neutron protection and reactor-scale validation,
and explicitly add cryogenic operation. The source's three-hour magnet float
time is not a plasma-discharge duration. Energetic-electron temperatures do not
describe thermal fusion-grade ions or net electrical output. Reactor-scale
validation is an explicit review requirement inferred from the laboratory scope;
neither the report nor the book qualifies an operating fusion power plant.

The actual admitted source is the author final report dated 10 March 2013,
deposited in DOE OSTI and captured through verified TLS. It is distinct from
the identified 2010 Nature Physics paper, whose full original was unavailable
and is not admitted as source-inspected evidence. All twelve report text pages
and complete selected book pages1043–1046 were read; two relevant pages were
rendered and visually inspected. Report funding does not establish blanket
original redistribution permission. Originals, extracts, figures and tables stay
private; the retained book keeps its unknown retrieval timestamp. All complete-
entry reviews and typed maturity/evidence fields remain pending.

Five compact-torus and pinch entries add 29 inspected citations: five naming
observations, twenty physical statements across fifteen fields and four bounded
experimental-history observations. One new IAEA country-report collection is
added; the retained Fusion Physics original and its unknown retrieval date stay
unchanged.

FRC has predominantly poloidal field, a reversal surface and closed interior
surfaces, with open exterior field lines. Weak toroidal-field variants remain
distinct from near-force-free spheromaks. High beta and simply connected geometry
do not establish confinement quality, reactor gain or universally simple systems.
Losses, rotation/tilt modes and current sustainment have separate limits;
fluid stability predictions and resilient kinetic experiments must be distinguished.

Spheromaks carry poloidal and toroidal fields. The engineering advantage now
names a simply connected vessel without interlocking toroidal-field coils.
It does not exclude gun electrodes, bias coils or other central components.
Formation can have wandering field lines and strong heat loss; helicity injection
may sustain current while perturbing surfaces. Measured SSPX current amplification
and projected reactor requirements are different quantities. Neither modeled
transport nor historical electron temperatures qualify a fusion power plant.

Z-pinch uses axial current and azimuthal field for radial compression; simple
basic geometry does not remove sausage/kink instability or pulsed-power
engineering. Theta pinch instead uses azimuthal current induced by rapidly changing
axial field. Its challenge now distinguishes axial losses in linear devices from
instability in toroidal experiments, replacing an unsupported general repetition
claim. The historical Los Alamos programme is reported through 1976, not as
current operation.

Dense plasma focus forms a transient pinch after axial sheath acceleration and
radial collapse in coaxial geometry. Neutron emission can involve thermal and
fast-ion beam-target contributions. The challenge explicitly names repeatable
neutron output, driver-to-radiation efficiency and electrode heat loads.
These are radiation-source operating concerns, not a claim of net fusion power
or electrical conversion. Improved historical devices reported repeatable output;
the concern is not a universal failure to reproduce neutron pulses.

The actual new original is Dense Magnetized Plasmas, IAEA-TECDOC-1699, published
in April 2013 from a coordinated research project spanning 2001–2006.
Selected Gribkov–Jednorog, Scholz and Tartari et al. sections were inspected,
with frontmatter and explicit printed-page mappings. PF-6 operation near one
pulse per second is distinct from component repetition-rate tests and lifetime
expectations. PF-1000 capacitor capacity is distinct from particular discharge
energies. The small-device electrode heat measurements do not define universal
DPF scaling; heat can persist even without a good pinch.

Full selected book pages253–255,1013–1031 and1046–1049 and the specified
country-report sections were read. Three relevant original pages were rendered
and visually inspected. The entire lengthy publications were not read.
Protected original figures, extracts and PDFs remain private. Legacy LLNL and
2023 DPF reference URLs remain, but their unread full originals supply none of
these new claims. All complete-entry and typed maturity/evidence reviews remain
pending.

Six shear-stabilized pinch and inertial-confinement entries add 37 inspected
citations: six naming observations, twenty-five physical statements across
eighteen fields and six bounded historical observations. Five original articles
or reports are added; the retained Fusion Physics original and its unknown
retrieval date stay unchanged.

Axial flow shear mitigates pinch instabilities under measured conditions.
FuZE neutron emission during a quiescent interval does not establish net power,
universal high-current stability or exclusion of every beam-target contribution.
Current-generated confinement fields reduce reliance on external confinement
coils; electrodes, return current and driver hardware remain. Longer burn,
scaling and electrode erosion are explicit research concerns.

Direct drive ablates the capsule through laser absorption and heat transport.
Direct coupling avoids hohlraum conversion, but irradiation imprint and
hydrodynamic instability remain. Historical OMEGA measurements do not prove
ignition or all-wavelength stabilization.

Indirect drive converts laser energy into hohlraum x-rays. The December 5,
2022 NIF experiment reported target gain 1.5 from 2.05 MJ of delivered laser
energy and about 3.1 MJ of fusion yield. Target gain has a different denominator
from capsule gain, fuel gain and facility energy consumption. The result does
not establish net electricity, a commercial repetition rate or a qualified
power-plant chamber. Driver recirculation and repeated debris/thermal/optic
handling remain plant requirements.

Fast ignition now explicitly describes a separate pulse intended to ignite
compressed fuel. Compression/heating separation is an optimization concept;
cone-guided heating and enhanced neutrons are distinct from achieved ignition.
Transport and localized deposition into the dense core remain limiting issues.

Shock ignition's strength now names potentially higher target gain from
separate compression and ignition phases. The inspected author-version paper
reports OMEGA-EP disk-plasma experiments, not an ignited compressed capsule.
Early pump depletion and the proposed SBS saturation mechanism are distinguished;
hot electrons need not be universally detrimental.

Heavy-ion efficiency and repetition are potential driver advantages. The 1988
HIFSA study modeled complete systems, while MBE-4 tested accelerator components.
Proposed beam compression, transport and focusing studies do not demonstrate a
complete driver, target ignition or current economic performance.

The inspected originals comprise the 2019 FuZE author version, 2020 Z-pinch
perspective, 2024 NIF publisher article in author-institution custody, 2019
shock-experiment author version and 1988 heavy-ion report. Bibliographic versions,
printed-page locators and measured-versus-modeled boundaries remain explicit.
Five relevant pages were rendered and inspected. Selected book and article
pages were read; entire lengthy publications were not claimed fully inspected.
Original figures, PDFs and extracts stay private. Whole-entry and typed
maturity/evidence reviews remain pending.

Impact-driven inertial fusion adds seven inspected statements from two
original reports. The mechanical gas-gun route supplies one-sided pressure
drive. Projectile velocity, planarity and integrity vary between experiments;
mechanical failures and confidential target details limit interpretation.
Its challenge now identifies projectile velocity, integrity and target
compression rather than claiming a demonstrated repetition constraint.

The 2022 First Light Fusion report gives DD-neutron evidence from selected
validation shots. Nine operational DD targets are a subset of twenty-one
experiments, not twenty-one fusion successes. Time-of-flight fitting uses a
selected subset and assumed neutron mass; yield inference neglects scattering.
Company-reported UKAEA participation does not substitute for a separately
obtained independent review. No target ignition, net energy, electricity or
current operating status follows from these historical measurements.

The two-page IAEA 2010 report describes a distinct laser-accelerated impact
route. Experimental foil collisions and a two-dimensional ignition simulation
remain separate. The ignition calculation neglects acceleration and implosion;
its driver-energy estimate assumes high coupling and reduced fuel energy.
Those estimates and velocities are not transferred to the gas-gun experiment.

Selected First Light pages and the complete two-page IAEA synopsis were
inspected; the complete ninety-page company report was not claimed read.
Two original-page schematics were visually inspected. Original PDFs, extracts
and figures remain private. All prior citations, source objects, typed labels
and historical audits are preserved; whole-entry review remains pending.

Pulsed-power and magnetized-liner concepts add twenty-six inspected statements
from five original sources. Z-pinch indirect drive supplies X-rays to a
separate capsule environment. The 2000 source measures radiation output and
hohlraum heating; these are not fusion yield or target gain. Radiation
uniformity and hohlraum wall motion are its documented constraints. Modeled
wall-motion reduction remains distinct from measured diagnostic-hole closure.

MagLIF instead compresses laser-preheated, magnetized fuel within a metal
liner. The 2014 author manuscript describes integrated and null experiments,
including a higher-density shot without significant yield. Neutron and X-ray
diagnostics support a thermonuclear interpretation; selected spectral fits,
possible mix, liner stability and modeled laser transmission constrain it.
Magnetic thermal insulation is a mechanism, not a universal measured loss
reduction. Repetitive operation remains a design challenge.

The IAEA 2022 proceedings contain contributions from a 2018 workshop.
General Fusion's liquid-metal chapter describes piston-driven cavity
compression, shielding and subsystem development. Its integrated demonstration
plant was proposed in that account. Neither its design language nor subsystem
reports establish integrated liquid-liner fusion or present operation.
The separate LM26 author preprint uses a solid lithium liner around a
spherical-tokamak deuterium plasma. Its v2 arXiv stamp is 30 June 2026 and
its manuscript date is 2 July 2026. Those dates are preserved as observed.
LM26 does not qualify liquid-liner or FRC performance, commercial liner
replacement, net energy or independently accepted Atlas review.

The fixed 2018 PJMIF v1 author preprint describes a stand-off jet driver
and conditional target-compression calculations. Target creation is assumed;
HELIOS models magnetized thermal transport through a conductivity multiplier.
Jet merging, uniformity, timely target engagement and unexplained modeled
energy flows require further work. Calculated heating and gains are not
integrated experimental target heating or measured energy coupling.

Selected original pages and three original-page renders were inspected;
complete documents are not claimed read. The attempted 2024 MagLIF PDF
returned 404 and is not admitted. Originals and extracts remain private.
All prior citation/source objects, typed labels and historical audits are
preserved. Whole-entry assessment remains pending.

Pulsed FRC compression and electrostatic neutron-source concepts add twenty-two
inspected statements from five original sources. The fixed 2025 FRC author
preprint compares two-dimensional MHD and kinetic-ion merging simulations.
Increasing mirror fields aids merging, but initial separation, surrounding
plasma, over-compression and stability constrain integration. Background Trenta
diagnostics and extrapolated scaling remain distinct from the new simulation
results. Complete merging and plasma stability replace unsupported
energy-recovery wording; this source does not establish integrated energy
recovery or measured reactor gain.

The Japanese 2018 IEC review describes ions accelerated through a physical
grid, with charge-exchange neutrals and background gas contributing to fusion.
Grid heating, sputtering, outgassing and feedthrough field distortion constrain
operation. Its historical neutron-source reports and source comparisons do not
establish an energy-producing IEC reactor. Original-page rendering resolves
Latin font extraction errors; the Japanese mechanism text was inspected.

The actual Polywell source is the fixed 2014 v1 author preprint. The attempted
2015 APS PDF returned HTTP 403 and is not admitted. Transient electron
confinement inferred from X-ray diagnostics does not demonstrate sustained ion
confinement, ion acceleration efficiency or a reactor power balance. The
potential outward-ion energy reduction is a proposed mechanism. It replaces
the previous unqualified physical-grid advantage. Speculative reactor outputs
retain their assumed-loss and ion-conversion boundaries.

The IAEA 2012 report documents compact DD/DT accelerator targets, electrical
switching, applications, target heating/loading and tritium handling. Its IEC
power percentage and secondary WB-6 claims are not transferred to accelerator
generators or the Polywell experiment. Stopping neutron emission does not
remove activated-material radiation.

A fixed 2024 P385 author preprint reports detector measurements and MCNP
source-rate inference, distinct from its later journal publication. Atlas
derives a bounded comparison: 70 microampere at 130 kV and 90 microampere at
140 kV imply 9.1 W and 12.6 W accelerator-beam input. The inferred
4.5e8 and 8.2e8 DT neutrons per second, with the IAEA 17.586 MeV reaction
energy, imply approximately 0.00127 W and 0.00231 W fusion output.
These ratios, approximately 1.4e-4 and 1.8e-4, exclude support-system
power and thermal conversion. They describe these device examples and are
not universal efficiency values. TRIM ion stopping, assumed target composition
and measured-inferred yields remain distinct; the model overpredicts measured
rates. No net-energy claim follows.

Selected original pages and three original-page renders were inspected; full
document reading is not claimed. Originals and extracts remain private.
All prior citation/source objects, typed labels and historical audits remain
preserved. Complete entry assessment is still pending.
Fusion-fission coupling and integrated nuclear energy systems add twenty-seven
inspected statements for six entries. The DOE 2009 workshop report separates
energy multiplication, transmutation and fuel-breeding missions. Driver duty,
materials, fuel fabrication and separations remain engineering constraints.
Transmutation does not eliminate geological disposal. The report includes
skeptical whole-system comparisons; proposed benefits are not operating proof.

The IAEA 2015 ADS report couples accelerator, spallation target and subcritical
fission assembly. Beam current controls the external source. Target damage and
accelerator availability remain constraints; dated MYRRHA/XADS design
requirements are not achieved commercial performance.

The nuclear-renewable report was printed in December 2022. It treats integrated
energy services and controls, with economics dependent on regional resources,
demand and markets. These are overlapping integration facets.

The November 2024 hydrogen report supports nuclear process-energy supply and
heat-exchanger isolation. Coupled qualification includes chemical hazards and
radioactive interfaces. Nuclear heating does not make fossil feedstocks carbon
free. Electrically heated test-plant and HTTR project plans remain dated plans.

Selected original pages and three diagrams were inspected. Originals and
extracts remain private; no complete entry or current maturity approval follows.
Existing hybrid catalogue hashes match all four captures. Exact original titles
replace the incorrect hydrogen and duplicate nuclear ADS catalogue titles.
All prior citations, source objects, typed labels and historical audits remain.

Four externally driven fusion configurations add seventeen inspected statements
binding twelve physical fields. Armour's NASA report is dated 2007 by the
original NASA metadata; its title and author replace an incorrect Petitjean/1988
catalogue attribution. Compact muonic molecules permit observed reactions at low
bulk temperature, while finite muon lifetime, sticking and production energy
limit their use. The report's energy estimates remain historical.

The June 2020 NASA theory and experiment reports have separate roles. The
experiment supplies bremsstrahlung and photoneutrons to activate a small portion
of the deuterium in a dense metal target. Its proposed future work calls for
further neutron-spectrum corroboration and identification of higher-energy
neutron sources. Local repeat measurements do not establish independent
replication or a closed reactor energy balance.

Chen et al.'s 2025 article combines an external accelerated deuterium beam with
electrochemical palladium loading. A reported relative neutron-rate increase is
distinct from net energy gain. The original XML uses its actual named sections,
with no fabricated PDF pages. Loading characterization was separate; the D/Pd
ratio was not measured directly during the fusion experiment.

Naranjo et al.'s 2005 paper reports a compact neutron burst driven by a thermal
cycle and explicitly excludes useful power production. Actual original pages,
including figures and printed labels, were inspected. All originals, XML and
page renders remain private. Whole-entry review and typed classifications stay
pending. Catalogue and original-custody bibliographic descriptions agree while
original paths, hashes, sizes and not_assessed redistribution rights are preserved.

Three disputed nuclear configurations add eighteen inspected statements across
nine physical fields. Pd-D electrolysis and gas-loaded metal claims remain
unconfirmed; controlled calorimetry and nuclear diagnostics make their hypotheses
testable without validating nuclear heat. DOE's November 1989 assessment is
retained as the 1999 NCAS Internet edition, with actual browser page labels.
The 2019 Nature perspective separates null cold-fusion results from externally
driven plasma fusion and states its loading and experimental limits.

Callisto's electrochemical summary reports failed replications and measurement,
heat-transfer and chemical-energy artifacts. Its historical announcement-year
typo is not adopted. The gas-loading report is dated 11 February 2024 on its
cover; it focuses on Pd-D and distinguishes negative results in examined
conditions from the authors' broader belief. Some sections are explicitly
omitted. Calorimeter sensitivity, untested materials and thin-film detector
assumptions limit inference beyond those experiments.

Fomitchev-Zamilov's 2012 cavitation preprint corrects a Taleyarkhan attribution.
It describes models, prototypes and prospective success criteria rather than
independently accepted power production. Shapira and Saltmarsh's 2002 repeat
used the same apparatus with some original authors and found no correlated
2.5 MeV neutron signal, with explicit random-coincidence and background bounds.
They did not measure tritium. These named null results do not prove every
conceivable cavitation experiment impossible. Full source titles and custody
descriptions agree; unknown retrieval dates and all whole-entry review flags
remain unchanged. Originals and figures are not redistributed.

Four nuclear-propulsion applications add sixteen inspected statements across
twelve physical fields. Finseth's February 1991 Rover review documents actual
ground tests, hydrogen heating and nozzle expansion. Fuel corrosion, vibration
and thermal stress constrain endurance. Electrically heated fuel cycles, fuel-test
furnaces, ideal-vacuum estimates and cancelled RIFT flight plans remain distinct
from nuclear rocket operation and completed flight qualification.

The FFRE conference abstract was published in November 2014; its 2015 NTRS
identifier is an acquisition label. The NIAC Phase I report describes the
2011–2012 study and models fragment escape, criticality and radiative cooling.
Theoretical velocity and estimated engine performance do not establish a built
rocket or a completed mission. Appendix A is referenced but absent from the
retained 18-page original; no missing calculations are reconstructed.

The 1994 antiproton paper proposes microfission/fusion ignition and describes
proof-of-principle work as underway. HiPAT identifies production, storage and
utilization requirements. Its initial hydrogen-ion tests are not antiproton
storage demonstrations. Design capacity, containment duration, compact-driver
advantages and planned experiments remain conditional.

The DFD Phase II report is dated 15 May 2019 on its cover; NASA's publication
metadata lists 31 August 2019. FRC electron-heating observations, projected
fusion-power allocations, a testbed photograph and nominal flight roadmaps
have separate evidential roles. Propulsion and onboard power are proposed
applications; the report does not verify a current fusion-core energy balance
or establish intrinsically hybrid nuclear physics.

Six genuine PDF captures retain their verified HTTPS retrieval dates and hashes.
Selected text pages and original figures were inspected; full-document reading
is not claimed. Original bodies and figures are not redistributed. All prior
citation/source objects, typed labels, historical audits and original-custody
metadata remain preserved; complete entry review remains pending.

Five solar, plasma and bioelectrochemical entries add twenty inspected
statements, binding the remaining fifteen physical fields. All 135 entries
now have citations for their principle, strength and challenge. Typed maturity
and evidence review and complete-entry review remain pending.

The 2022 solar tower paper demonstrates a ceria reactor within a pilot
sun-to-liquid process chain. Its reactor efficiency differs from the full
plant boundary. Rejected sensible heat, local cracking during 62 cycles and
projected recovery gains retain separate observational roles. Inconsistent
hydrogen/water labels in Table 1 are not adopted.

The OSTI manuscript is dated 29 January 2020. It separates a simplified
microkinetic CSTR model from packed-bed discharge experiments. Catalyst
contributions can enhance or suppress yields under different conditions.
Beyond bulk thermal-equilibrium yields require electrical input; they do not
violate thermodynamics or establish favorable full-system energy efficiency.
Repeated GC injections are not independent cross-laboratory reproducibility.

The fixed arXiv v1 preprint couples photovoltaic water electrolysis to
photothermal carbon-dioxide hydrogenation. Its laboratory efficiency uses
PV area allocated to consumed hydrogen rather than all installed PV area;
the outdoor efficiency uses its stated illuminated area. Six-day laboratory
stability and one dated outdoor test do not prove long-term endurance.
The prose, figure and methods disagree on one intermediate efficiency;
no disputed value becomes a general performance guarantee.

The MFC review distinguishes direct and mediated electron transfer and
describes both treatment applications and low power-density/scale-up limits.
The MEC cathode review was published online in October 2021 and collected
in a January 2022 issue. It distinguishes external electricity from substrate
chemical energy. Electricity-only efficiency above 100% is not energy
creation. The MEC challenge is narrowed from generic electrode fouling to
the explicitly supported catalyst poisoning and full-system energy accounting.
The review does not independently validate each experiment it cites.

Three genuine PDF and two genuine XML source bodies retain retrieval dates
and SHA-256. The inaccessible publisher MFC PDF was not admitted; the official
archive XML is a separate successful capture. XML sections have no invented
PDF page numbers. Selected text and original PDF figures were inspected,
without claiming full reading of all sources. Original bodies and figures
are not redistributed. All prior citation/source objects, typed labels and
historical audits are preserved; complete-entry review remains pending.

## Input contract: schema 1.2.0

The object has exactly `schema_version`, `taxonomy_sha256`, `sources` and
`records`. Every current entry appears once, in catalogue order. Each record
binds the exact current name, kind, family, principle, strength, challenge,
maturity, evidence and source URLs in `values`. Text fields require nonempty
single-line strings; source URLs require a nonempty array of anonymous HTTPS
links. An object in a text field cannot be accepted by updating the hash and
binding the same malformed value. This is a drift guard, not an
assertion that all those fields have been verified. `complete_entry_review` is
always false; entries without inspected statements retain an empty array.

Citation topics are `classification`, `fuel-state-classification`,
`historical-operation`, `operating-mode`, `principle`, `strength` and `challenge`.
The first four topics describe bounded observations. For the last three, the
statement must exactly match the complete corresponding current field; a short
category label cannot stand in for the field. Its source URL must also occur
in the entry's current references. This binding prevents silent
wording drift; it does not replace source inspection or independent review.
Each citation retains its own identity, statement, source ID, section,
`pdf_pages`, `printed_pages`, scope, `reviewed_on` date and
`author-source-inspection` review basis. Anonymous HTTPS links, distinct
identities, valid dates and page numbers within the original document are
required. Unsupported schemas, unknown fields, stale hashes, mixed catalogue
values, incomplete entry sets and unused source definitions fail validation.

Source formats are `pdf`, `html` and `xml`. A PDF has a positive
`page_count` and nonempty one-based `pdf_pages`, paired with printed labels.
HTML and XML have `page_count: 0` and empty PDF/printed-page arrays; their
`section` identifies the inspected heading or named XML section. XML bytes
are hashed as XML, without changing the format or inventing PDF pagination.
No source original is distributed by the export or detail renderer.

Each source requires `capture_method`: `publisher-tls` requires a valid UTC
`captured_at` timestamp, while `retained-source-review` requires null. The
citation's `reviewed_on` date records inspection separately and cannot precede
a known retrieval. Unknown retrieval dates are never filled from file times,
PDF creation metadata or inspection dates. These are evidence declarations
checked for consistency, not cryptographic proof of a publisher connection.

When taxonomy content changes, reconcile every bound record and inspect the
affected source claims before updating the hash. Merely replacing the hash
cannot bypass semantic drift checks and does not establish new evidence.

## Export and offline presentation

```bash
node 04_interactive_presentation/scripts/export_taxonomy.cjs
node 04_interactive_presentation/scripts/export_taxonomy.cjs --root /path/to/complete/candidate
```

The exporter resolves inputs from the selected repository rather than the
working directory. Its public `exportTaxonomy(repositoryRoot)` API uses the
same complete catalogue and validation path. `readCitations(repositoryRoot,
rows)` returns a Map of all entry IDs to resolved statements. Both APIs throw
on invalid inputs. Input validation finishes before any existing product is
written. Filesystem write errors still require restoring or rebuilding the
affected products; this is not a multi-file filesystem transaction.

The existing three products are retained: the source TSV adds a JSON-valued
`claim_citations` column; audit JSON and offline JavaScript use schema 1.3.0
and add `claim_citations` and false `complete_entry_review` to each record.
Resolved statements also expose `source_capture_method` and
`source_captured_at`. Historical audit fields are unchanged. No raw publisher
document is embedded.

The actual detail dialog calls `AtlasTaxonomyCitations.render(citations)` from
[the native presentation script](../../04_interactive_presentation/taxonomy-claim-sources.js).
It displays each statement, linked source, exact locator, scope and inspection
date, plus a known retrieval date or an explicit unknown-date label;
entries without citations show a pending-review message. PDF links include a
page fragment where possible. This exported HTML serializer is also exercised
on Node; those tests do not replace acceptance in a native browser.

The [presentation validator](../../04_interactive_presentation/validate.sh)
runs dedicated native tests for metadata, exporter and detail serialization,
with 100 per cent line, branch and function thresholds. Tests use the complete
actual 135-entry catalogue, its 599 citations, real file copies and CLI processes,
including corruptions that must preserve all existing products. CI invokes
this same validator through `make validate`; there is no separate unwired gate.

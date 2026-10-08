// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — 04_interactive_presentation/data/taxonomy-expanded.js
/* English reactor taxonomy. Categories overlap: these are indexed architectures,
 * subtypes, process modes and system concepts, not a count of mutually exclusive
 * inventions. Fuel choices, vendors and size classes are facets, not extra types.
 * Evidence refers to the stated process/configuration, never automatically to a
 * commercial power plant. Scores without a defensible common metric are null.
 * Source coverage is introductory; source audit and facility linkage are ongoing.
 */
(function () {
  "use strict";
  const sources = {
    nrc: "https://www.nrc.gov/cdn/legacy/reading-rm/training/reactor-concepts-training-course.pdf",
    nrcBwr:
      "https://www.nrc.gov/sites/default/files/doc_library/cdn/legacy/reading-rm/basic-ref/students/for-educators/03.pdf",
    passiveWater:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TCS-69web.pdf",
    pwrExperience:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/RDS-2-45_web.pdf",
    waterSmrValidation:
      "https://nucleus.iaea.org/sites/nexshare/Focus%20Group/WCR%20FG/LW-SMR%20FG_Working_paper.pdf",
    pris: "https://www-pub.iaea.org/MTCD/Publications/PDF/te_1544_web.pdf",
    candu: "https://unene.ca/resources/the-essential-candu/",
    hwr: "https://www-pub.iaea.org/MTCD/publications/PDF/TRS407_scr/D407_scr1.pdf",
    gasDecommissioning:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/te_1043_prn.pdf",
    graphiteHistory:
      "https://nucleus.iaea.org/sites/graphiteknowledgebase/wiki/Guide_to_Graphite/History%20of%20Graphite%20in%20the%20UK%20Nuclear%20Industry.aspx",
    graphiteAgeing:
      "https://www.onr.org.uk/our-work/what-we-regulate/operational-power-stations/current-issues/graphite-core-ageing",
    rbmkHistory: "https://pub.iaea.org/MTCD/publications/PDF/Pub913e_web.pdf",
    htgr: "https://www-pub.iaea.org/MTCD/Publications/PDF/te_1198_prn.pdf",
    fast: "https://www-pub.iaea.org/MTCD/Publications/PDF/te_1691_web.pdf",
    gif: "https://www.gen-4.org/generation-iv-criteria-and-technologies",
    gifScwr:
      "https://www.gen-4.org/generation-iv-criteria-and-technologies/super-critical-water-reactors-scwr",
    gifVhtr:
      "https://www.gen-4.org/generation-iv-criteria-and-technologies/very-high-temperature-reactor-vhtr",
    msr: "https://doi.org/10.13182/NT15-124",
    msrStatus:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/STI-DOC-010-489_web.pdf",
    saltCoolants:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TE_1696_web.pdf",
    wave: "https://doi.org/10.1016/J.ENG.2016.01.024",
    wavePaper: "https://www.engineering.org.cn/engi/EN/1159828159715664823",
    fusion: "https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1562_web.pdf",
    solarTower2022:
      "https://www.research-collection.ethz.ch/server/api/core/bitstreams/81f8118a-f03e-44fb-9aed-54f5709f388c/content",
    plasmaMehta2020: "https://www.osti.gov/servlets/purl/1803043",
    pvPhotosynthesisV1: "https://arxiv.org/pdf/2204.04971v1",
    mfcReview2022:
      "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8981509/fullTextXML",
    mecCathode2021:
      "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10114852/fullTextXML",
    propulsionRover1991:
      "https://ntrs.nasa.gov/api/citations/19920005899/downloads/19920005899.pdf",
    propulsionAntiproton1994:
      "https://ntrs.nasa.gov/api/citations/19950002761/downloads/19950002761.pdf",
    propulsionFFREAbstract2014:
      "https://ntrs.nasa.gov/api/citations/20150002578/downloads/20150002578.pdf",
    propulsionFFRE2012:
      "https://ntrs.nasa.gov/api/citations/20160010095/downloads/20160010095.pdf",
    propulsionDFD2019:
      "https://ntrs.nasa.gov/api/citations/20190031807/downloads/20190031807.pdf",
    propulsionHiPAT2000:
      "https://ntrs.nasa.gov/api/citations/20010020151/downloads/20010020151.pdf",
    contestedDOE1989:
      "https://commons.wikimedia.org/wiki/File:Cold_Fusion_Research_-_ERAB_-_1989.pdf",
    contestedGoogle2019: "https://doi.org/10.1038/s41586-019-1256-6",
    contestedCallistoElectrochemical:
      "https://callisto.report/reports/callisto-electrochemical-loading-summary.pdf",
    contestedCallistoPressure:
      "https://callisto.report/reports/callisto-pressure-loading-full.pdf",
    contestedShapira2002: "https://doi.org/10.1103/PhysRevLett.89.104302",
    contestedCavitation2012: "https://arxiv.org/abs/1209.2407",
    lowMuon2007:
      "https://ntrs.nasa.gov/api/citations/20080040752/downloads/20080040752.pdf",
    lowLatticeTheory2020:
      "https://ntrs.nasa.gov/api/citations/20205001617/downloads/TP-20205001617.pdf",
    lowLatticeExperiment2020:
      "https://ntrs.nasa.gov/api/citations/20205001616/downloads/TP-20205001616.pdf",
    lowBeam2025:
      "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12367529/fullTextXML",
    lowPyro2005: "https://fire.pppl.gov/cyrstal_fusion_nature.pdf",
    hybridDOE2009:
      "https://science.osti.gov/-/media/fes/pdf/workshop-reports/Ff_hybrid_report_final.pdf",
    hybridADS2015:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1766_web.pdf",
    hybridNR2022:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/PUB2041_web.pdf",
    hybridH2024:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TE-2075web.pdf",
    frcHybrid2025: "https://arxiv.org/pdf/2501.03425v1",
    iecJstage2018:
      "https://www.jstage.jst.go.jp/article/lsj/46/10/46_589/_pdf/-char/en",
    ngIAEA2012: "https://www-pub.iaea.org/MTCD/Publications/PDF/P1535_web.pdf",
    polywellOriginal2014: "https://arxiv.org/pdf/1406.0133v1",
    dtGenerator2024: "https://arxiv.org/pdf/2406.18607v1",
    linerZDriver2000: "https://www.osti.gov/servlets/purl/759878",
    linerMagLIF2014: "https://www.osti.gov/servlets/purl/1146936",
    linerIAEA2022:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1997web.pdf",
    linerPJMIF2018: "https://arxiv.org/pdf/1803.03323v1",
    linerLM262026: "https://arxiv.org/pdf/2606.23974v2",
    impactFirstLight2022:
      "https://firstlightfusion.com/wp-content/uploads/2026/09/first_light_fusion_experimental_white_paper.pdf",
    impactIAEA2010:
      "https://www-pub.iaea.org/mtcd/meetings/PDFplus/2010/cn180/cn180_papers/ife_p6-04.pdf",
    shearFuZE2019: "https://arxiv.org/pdf/1806.05894v4",
    zPinchPerspective2020: "https://www.osti.gov/servlets/purl/1799021",
    nifTargetGain2024:
      "https://ora.ox.ac.uk/objects/uuid%3A6bda0302-497e-4ba6-ad71-2f088a0add19/files/srr1720094",
    shockPumpDepletion2019: "https://arxiv.org/pdf/1909.00094v1",
    heavyIonDriver1988: "https://www.osti.gov/servlets/purl/6984282",
    densePlasmaDmp:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1699_web.pdf",
    ldxFinalReport: "https://www.osti.gov/servlets/purl/1095287",
    w7xTransportPaper:
      "https://pure.tue.nl/ws/portalfiles/portal/190959427/s41586_021_03687_w.pdf",
    fusionTechnology:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/PUB1945_web.pdf",
    stppPaper:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/csp_019c/pdf/ft1_5.pdf",
    fusionTypes:
      "https://nucleus.iaea.org/sites/connect/FUSEpublic/SitePages/Fusion-Technologies.aspx",
    helical: "https://www-lhd.nifs.ac.jp/pub/LHD_Project_en.html",
    lle: "https://www.lle.rochester.edu/inertial-confinement-fusion/",
    mif: "https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1997web.pdf",
    dipole: "https://doi.org/10.1016/j.fusengdes.2006.07.002",
    rfp: "https://library.psfc.mit.edu/catalog/online_pubs/iap/iap2012/freidberg.pdf",
    spheromak: "https://str.llnl.gov/sites/str/files/2024-04/1999.12.pdf",
    polywell: "https://doi.org/10.1103/PhysRevX.5.021024",
    iec: "https://doi.org/10.2184/lsj.46.10_589",
    neutronGenerator:
      "https://nucleus.iaea.org/sites/nuclear-instrumentation/Pages/neutrons.aspx",
    dpf: "https://doi.org/10.1007/s10894-023-00345-z",
    pjif: "https://arxiv.org/abs/1803.03323",
    maglif: "https://doi.org/10.1063/5.0206222",
    zicf: "https://www.sandia.gov/research/publications/details/dynamics-of-a-z-pinch-x-ray-source-for-heating-icf-relevant-hohlraums-to-12-2000-07-10/",
    doeFusion: "https://www.energy.gov/fusion/articles/fusion-st-roadmap",
    mit: "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/pages/lecture-notes/",
    chemMitBatch:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/283b16fdf984efdf4e6f5ecccffac44a_lec07_02282007_w.pdf",
    chemMitCstr:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/9289fe86a4778895a9584bb4fca5c5c2_lec05_02212007_g.pdf",
    chemMitPfr:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/d4c77250b11a07b28ed55f826c83b376_lec08_03022007_g.pdf",
    chemMitSeries:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/7f66d10fe91facfed4a32695695f2996_lec09_03072007_w.pdf",
    chemMitRtd:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/c74dac1784fab22deb39830c06a27fec_lec10_03092007_w.pdf",
    chemMitNonisothermal:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/6e37d01fbdf96ce9a42a085c48bb9a26_lec11_03142007_g.pdf",
    chemHseHsg143: "https://www.hse.gov.uk/pubns/priced/hsg143.pdf",
    chemHseIndg254: "https://www.hse.gov.uk/pubns/indg254.pdf",
    chemBuffaloNetworks:
      "https://wwwresearch.sens.buffalo.edu/karetext/unit_29/learning/29_Info.pdf",
    chemUowTwoCstrAbstract:
      "https://documents.uow.edu.au/~mnelson/abstracts.dir/2007.html",
    chemImaReactiveCrystallisation:
      "https://imagroup.com/insights/development-of-an-automated-multi-stage-continuous-reactive-crystallization-system-with-inline-pats-for-high-viscosity-process/",
    chemSquStepFeed:
      "https://squ.elsevierpure.com/en/publications/an-analysis-of-a-standard-reactor-cascade-and-a-step-feed-reactor/",
    multiMitPorousPacked:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/4fea4f4e0f38526c4fa7f2d55c602427_lec21_05022007_g.pdf",
    multiQubSlurryChapter:
      "https://pure.qub.ac.uk/en/publications/three-phase-slurry-reactors/",
    multiFoglerLaboratory:
      "https://kinetics.engin.umich.edu/05chap/html/05prof3.htm",
    multiUopCcr:
      "https://uop.honeywell.com/content/dam/uop/en-us/documents/product-services/catalysts/refining/reforming/uop-ccr-platforming-motor-fuel-datasheet.pdf?download=true",
    multiNetlMovingModel:
      "https://www.netl.doe.gov/projects/files/201.007_%20MB%20CLC%20Model_Final_Public.pdf",
    multiOstimovingAttrition: "https://www.osti.gov/servlets/purl/419318",
    multiFoglerFluidised:
      "https://kinetics.engin.umich.edu/12chap/html/12prof2a.htm",
    multiNptelFluidisedHeat:
      "https://archive.nptel.ac.in/content/storage2/courses/103103026/module2/lec18/1.html",
    multiNptelFluidisedFaq:
      "https://archive.nptel.ac.in/content/storage2/courses/103102012/downloads/faqs%20for%20module%209.pdf",
    multiNetlCirculatingOxygen:
      "https://netl.doe.gov/projects/files/201.007_HTHC%20OC_Screening_Study_Public_Final.pdf",
    multiFoglerTrickle:
      "https://kinetics.engin.umich.edu/12chap/html/12prof.htm",
    multiPurdueTrickleAbstract:
      "https://docs.lib.purdue.edu/dissertations/AAI10100487/",
    multiPittSlurryScale: "https://sites.pitt.edu/~rapel/Inga.html",
    multiFoglerSlurry:
      "https://kinetics.engin.umich.edu/12chap/html/slurry.pdf",
    multiBubbleExperimental: "https://arxiv.org/pdf/2203.07417",
    multiNptelAirDriven:
      "https://archive.nptel.ac.in/content/storage2/courses/102103016/module4/lec36/4.html",
    multiDtuAirliftExperiments:
      "https://backend.orbit.dtu.dk/ws/portalfiles/portal/9855372/PROCESS_Mads%20Orla%20Alb_k_PhD%20Thesis.pdf",
    multiAirliftHydrodynamics:
      "https://mdpi-res.com/d_attachment/energies/energies-14-04329/article_deploy/energies-14-04329.pdf",
    flowSftr: "https://pmc.ncbi.nlm.nih.gov/articles/PMC13159419/",
    flowGasSlug: "https://pmc.ncbi.nlm.nih.gov/articles/PMC4547489/",
    flowNumbering: "https://pmc.ncbi.nlm.nih.gov/articles/PMC5762165/",
    cultureMitChemostatFedBatch:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/cacb521f9f123abde3b9a448c5e17d56_lec13_03212007_w.pdf",
    cultureMitOxygenTransfer:
      "https://ocw.mit.edu/courses/10-37-chemical-and-biological-reaction-engineering-spring-2007/85477ce30129fae080056a95bf5b3cdd_lec19_04202007_w.pdf",
    cultureBioStemCellStirred:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC8156863/",
    cultureBioPerfusionExperiment:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC5532224/",
    cultureBioChemostatProtocol:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC3940325/",
    cultureBioChemostatSterility:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC11565388/",
    fogler: "https://websites.umich.edu/~elements/5e/asyLearn/bits.htm",
    slurry: "https://doi.org/10.1016/j.eng.2021.03.002",
    membrane:
      "https://mdpi-res.com/bookfiles/book/1347/Membrane_and_Membrane_Reactors_Operations_in_Chemical_Engineering.pdf",
    micro: "https://pmc.ncbi.nlm.nih.gov/articles/PMC11434323/",
    doeElectrolysis:
      "https://www.energy.gov/cmei/fuels/hydrogen-production-electrolysis",
    fuelCellTypes: "https://www.energy.gov/cmei/fuels/types-fuel-cells",
    pnnlSyngas:
      "https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-29240.pdf",
    fuelcell:
      "https://netl.doe.gov/sites/default/files/netl-file/FCHandbook7.pdf",
    electrolyzer:
      "https://www.energy.gov/sites/default/files/2024-12/hydrogen-shot-water-electrolysis-technology-assessment.pdf",
    researchReactor:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1596_web.pdf",
    researchAnalysis:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/PUB1946_web.pdf",
    reactorDesign:
      "https://gnssn.iaea.org/main/bptc/BPTC%20Module%20Documents/Module04%20Design%20of%20a%20nuclear%20reactor.pdf",
    aqueousSolutions:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/te_1601_web.pdf",
    crocus: "https://www.epfl.ch/labs/lrs/facilities/crocus-reactor/",
    crocusCourse:
      "https://edu.epfl.ch/coursebook/en/radiation-and-reactor-experiments-PHYS-451",
    mainzMode: "https://www.en.triga.uni-mainz.de/betriebsmodus/",
    subcriticalAssembly:
      "https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1976web.pdf",
    sequencingBatch:
      "https://www.epa.gov/system/files/documents/2022-10/sequencing-batch-reactors-factsheet.pdf",
    wastewater:
      "https://www3.epa.gov/ghgreporting/help/tool2014/definitions/industrial-wastewater.html",
    chemicalLooping: "https://www.netl.doe.gov/node/7478",
    photo: "https://doi.org/10.1021/acs.iecr.9b00381",
    plasma: "https://doi.org/10.1016/j.gerr.2023.100004",
    plasmaHydrogenation:
      "https://engj.org/index.php/ej/article/download/4489/1271",
    plasmaMicrowaveProtocol:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC5613793/",
    plasmaGlidingExperiment:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC11191589/",
    plasmaTechnoeconomic: "https://pmc.ncbi.nlm.nih.gov/articles/PMC11320396/",
    plasmaThermalNetl:
      "https://netl.doe.gov/sites/default/files/2018-01/20170322_1300C_Presentation_FE0027102_SouthernResearch.pdf",
    plasmaGlidingDiagnostics:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC11269738/",
    polymer: "https://doi.org/10.1016/0009-2509(96)00024-3",
    polymerNptelProcesses:
      "https://archive.nptel.ac.in/content/storage2/courses/103103026/module4/lec38/3.html",
    polymerNptelTechnology:
      "https://archive.nptel.ac.in/content/storage2/courses/103103029/module7/lec37/1.html",
    polymerNptelEmulsion:
      "https://archive.nptel.ac.in/content/storage2/courses/103103029/module7/lec37/2.html",
    polymerDispersedTutorial:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC2967636/",
    polymerEmulsionMonitoring:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC7926705/",
    gasifier:
      "https://netl.doe.gov/sites/default/files/netl-file/24FECM_GAS_Wagner.pdf",
    thermoNetlTypes:
      "https://netl.doe.gov/sites/default/files/netl-file/1-2-1.pdf",
    thermoNetlHandbook:
      "https://www.netl.doe.gov/sites/default/files/2026-02/Gasification%20Handbook.pdf",
    thermoNetlWagner:
      "https://netl.doe.gov/sites/default/files/netl-file/24FECM_GAS_Wagner.pdf",
    thermoNrelTcpdu: "https://docs.nlr.gov/docs/fy09osti/44034.pdf",
    thermoNrelAging: "https://docs.nlr.gov/docs/fy22osti/80966.pdf",
    thermoPyrolysisExperiment:
      "https://pmc.ncbi.nlm.nih.gov/articles/PMC4550300/",
    thermoScwgRetained: "https://arxiv.org/abs/1901.09466",
    pyro: "https://www.nrel.gov/docs/fy09osti/44034.pdf",
    hydro: "https://arxiv.org/abs/1901.09466",
    digester:
      "https://www.epa.gov/sites/production/files/2014-12/documents/agstar-handbook.pdf",
    adOperator:
      "https://www.epa.gov/sites/default/files/2020-11/documents/agstar-operator-guidebook.pdf",
    adUasb: "https://pmc.ncbi.nlm.nih.gov/articles/PMC7355771/",
    adDesign:
      "https://www.epa.gov/agstar/anaerobic-system-design-and-technology",
    bio: "https://doi.org/10.1016/j.cjche.2020.12.004",
    hybrid:
      "https://science.osti.gov/-/media/fes/pdf/workshop-reports/Ff_hybrid_report_final.pdf",
    ads: "https://doi.org/10.1146/annurev.nucl.48.1.505",
    integrated: "https://doi.org/10.2172/1333006",
    muon: "https://doi.org/10.1016/0375-9474(92)90412-D",
    lattice:
      "https://ntrs.nasa.gov/api/citations/20205006546/downloads/LCF%20Workshop%20-%20May%2021%202020%20-%20Final%20Public.pdf",
    beam: "https://doi.org/10.1038/s41586-025-09042-7",
    lenr: "https://doi.org/10.1038/s41586-019-1256-6",
    callisto: "https://callisto.report/",
    bubble: "https://doi.org/10.1103/PhysRevLett.89.104302",
    pyroFusion: "https://www.nature.com/articles/nature03575",
    antimatter: "https://ntrs.nasa.gov/citations/19950002761",
    fragment: "https://ntrs.nasa.gov/citations/20150002578",
    ntr: "https://ntrs.nasa.gov/citations/19920005899",
    dfd: "https://doi.org/10.1016/j.actaastro.2014.08.008",
    solar: "https://doi.org/10.1016/j.joule.2022.06.012",
    plasmaCatalysis: "https://www.osti.gov/servlets/purl/1803043",
    mfc: "https://doi.org/10.1039/D1RA08487A",
    mec: "https://doi.org/10.1016/j.enzmictec.2016.09.002",
    artificial: "https://arxiv.org/abs/2204.04971",
  };
  const builder = globalThis.AtlasTaxonomyConstruction.create(sources);
  const add = builder.add;
  add("fission", "Water-cooled fission", "nrc pris", [
    [
      "PWR",
      null,
      "deployed",
      "established",
      "Pressurised primary water transfers core heat to a separate steam system.",
      "Extensive operating experience",
      "High-pressure boundary integrity and spent-fuel handling",
      "architecture",
      { source: "nrc pris pwrExperience", reviewed_on: "2026-10-01" },
    ],
    [
      "Integral PWR",
      "PWR",
      "demonstrated",
      "demonstrated",
      "Most or all primary system components are integrated inside the reactor pressure vessel.",
      "Reduced external primary-circuit piping",
      "Inspection access and validation of natural-circulation designs",
      "subtype",
      {
        source: "nrc pris passiveWater waterSmrValidation",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "BWR",
      null,
      "deployed",
      "established",
      "Coolant boils in the core and supplies steam directly to the turbine.",
      "Direct steam cycle",
      "Two-phase stability and radioactive steam circuit",
      "architecture",
      { source: "nrc pris nrcBwr passiveWater", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fission", "Heavy-water fission", "candu pris", [
    [
      "PHWR / CANDU",
      null,
      "deployed",
      "established",
      "Heavy-water moderation supports pressure-tube cores with strong neutron economy.",
      "Fuel flexibility and online refuelling",
      "Pressure-tube ageing and heavy-water management",
      "architecture",
      { source: "candu pris hwr", reviewed_on: "2026-10-01" },
    ],
    [
      "Heavy-water pressure-vessel reactor",
      null,
      "demonstrated",
      "established",
      "A pressure vessel contains a heavy-water-moderated power-reactor core.",
      "Heavy-water neutron economy",
      "Heavy-water management and fuel-channel materials degradation",
      "architecture",
      { source: "hwr", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fission", "Graphite-moderated fission", "pris htgr", [
    [
      "Magnox gas-cooled reactor",
      null,
      "demonstrated",
      "established",
      "Carbon dioxide cools graphite-moderated fuel with magnesium-alloy cladding.",
      "Historical commercial operating experience",
      "Legacy decommissioning and materials limits",
      "architecture",
      { source: "pris htgr gasDecommissioning", reviewed_on: "2026-10-01" },
    ],
    [
      "Advanced gas-cooled reactor (AGR)",
      null,
      "deployed",
      "established",
      "Enriched uranium-oxide fuel with stainless-steel cladding supports higher-temperature carbon-dioxide cooling in a graphite-moderated core.",
      "Elevated thermal efficiency",
      "Graphite ageing and inspection constraints",
      "architecture",
      {
        source: "pris htgr graphiteHistory graphiteAgeing",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "RBMK pressure-tube reactor",
      null,
      "deployed",
      "established",
      "Graphite moderates a core cooled by boiling light water in individual pressure tubes.",
      "Online refuelling",
      "Design-specific reactivity feedback and fuel-channel integrity",
      "architecture",
      { source: "pris rbmkHistory", reviewed_on: "2026-10-01" },
    ],
    [
      "Prismatic HTGR",
      null,
      "demonstrated",
      "demonstrated",
      "Helium flows through graphite blocks containing coated-particle fuel.",
      "High-temperature heat and coated-particle fission-product barriers",
      "Fuel qualification and high-temperature components",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Pebble-bed HTGR",
      null,
      "deployed",
      "established",
      "Helium flows between graphite fuel spheres in a pebble-bed core.",
      "High-temperature output and potential continuous refuelling",
      "Dust, pebble handling and fuel accounting",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fission", "Advanced fission", "gif fast", [
    [
      "Sodium fast reactor",
      null,
      "deployed",
      "established",
      "Liquid sodium cools a fast-neutron core.",
      "Low-pressure cooling and fuel-cycle flexibility",
      "Sodium reactions and opaque-coolant inspection",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Lead fast reactor",
      null,
      "research",
      "research",
      "Liquid lead cools a fast-spectrum core.",
      "High boiling point",
      "Corrosion, freezing and structural loads",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Lead-bismuth fast reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Lead-bismuth eutectic provides liquid-metal cooling of a fast core.",
      "Lower melting temperature than pure lead",
      "Coolant chemistry and polonium management",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Gas-cooled fast reactor",
      null,
      "concept",
      "research",
      "A gas coolant removes heat from a fast-spectrum core; high-temperature designs target refractory fuel.",
      "Targeted high outlet temperature",
      "Decay-heat removal and fuel development",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Supercritical-water reactor",
      null,
      "concept",
      "research",
      "Water above its critical point serves as reactor coolant.",
      "Potentially efficient steam cycle",
      "Materials and heat transfer near the critical region",
      "architecture",
      { source: "gif gifScwr", reviewed_on: "2026-10-01" },
    ],
    [
      "Very-high-temperature reactor (VHTR)",
      "High-temperature gas reactor",
      "concept",
      "research",
      "Helium cools a graphite-moderated thermal-neutron core; higher-temperature process heat is a development target.",
      "Potential industrial high-temperature heat",
      "Materials qualification at target temperatures",
      "development class",
      { source: "gif gifVhtr htgr", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fission", "Salt-based fission", "msrStatus gif", [
    [
      "Thermal liquid-fuel molten-salt reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Fuel dissolved in molten salt supports a moderated thermal-neutron core.",
      "Low coolant pressure",
      "Fuel-salt chemistry, processing and containment",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Fast liquid-fuel molten-salt reactor",
      null,
      "concept",
      "research",
      "A liquid fuel-salt core is configured for a fast-neutron spectrum.",
      "Potential fuel-cycle flexibility",
      "Materials and integrated fuel treatment",
      "architecture",
      { reviewed_on: "2026-10-01" },
    ],
    [
      "Fluoride-salt-cooled high-temperature reactor",
      null,
      "research",
      "research",
      "Liquid fluoride salt cools solid fuel rather than carrying dissolved fuel.",
      "Low-pressure high-temperature heat removal",
      "Salt chemistry, component qualification and decay-heat removal",
      "architecture",
      { source: "msrStatus saltCoolants", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fission", "Advanced fuel-cycle concepts", "wave", [
    [
      "Breed-and-burn reactor",
      null,
      "concept",
      "research",
      "Fuel breeds fissile material that is consumed during extended irradiation.",
      "Potentially high fuel utilisation",
      "High fuel burnup and cladding irradiation exposure",
      "architecture",
      { source: "wave wavePaper", reviewed_on: "2026-10-01" },
    ],
    [
      "Traveling-wave reactor",
      "Breed-and-burn reactor",
      "concept",
      "research",
      "A proposed breeding-and-burning region propagates relative to the fuel inventory.",
      "Potential reduced external fuel processing",
      "Sustaining breed-and-burn reactivity and qualifying high-exposure fuel",
      "subtype",
      { source: "wave wavePaper fast", reviewed_on: "2026-10-01" },
    ],
    [
      "Standing-wave breed-and-burn reactor",
      "Breed-and-burn reactor",
      "concept",
      "research",
      "Fuel shuffling keeps the burning region approximately stationary in the reactor.",
      "Potentially simpler cooling with a stationary burning region",
      "High-burnup fuel qualification and fuel-handling equipment",
      "subtype",
      { source: "wave wavePaper", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fission", "Research-reactor configurations", "researchReactor", [
    [
      "Pool-type research reactor",
      null,
      "deployed",
      "established",
      "The core and irradiation positions are accessible within an open water pool used for shielding and cooling.",
      "Access to in-core and reflector irradiation positions",
      "Application-specific power, ageing and fuel management",
      "research-reactor geometry",
      {
        source: "researchReactor reactorDesign researchAnalysis",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Tank-type research reactor",
      null,
      "deployed",
      "established",
      "The core is contained in a closed tank within biological shielding.",
      "Controlled coolant boundary",
      "Inspection access and ageing management",
      "research-reactor geometry",
      {
        source: "researchReactor reactorDesign researchAnalysis",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Tank-in-pool research reactor",
      "Tank-type research reactor",
      "deployed",
      "established",
      "A core tank sits within a water pool, combining tank and pool arrangements.",
      "Design-specific separation of coolant or moderator regions",
      "Integrated inspection and cooling arrangements",
      "research-reactor geometry",
      {
        evidence_scope:
          "Established reactor architecture. This is a combination of the tank and pool geometries rather than a third independent geometry; it is indexed separately for discovery, not as an additional distinct principle.",
        reviewed_on: "2026-10-01",
        source: "researchReactor reactorDesign researchAnalysis",
      },
    ],
    [
      "Aqueous homogeneous reactor",
      null,
      "demonstrated",
      "established",
      "Fissile material is dissolved in a water-based solution that serves as the reacting fuel medium.",
      "Homogeneous liquid fuel and isotope-production potential",
      "Radiolysis, chemistry and containment",
      "liquid-fuel research architecture",
      {
        evidence_scope:
          "The fuel-state classification cross-cuts pool and tank geometry. IAEA-TECDOC-1601 documents historical solution reactors and isotope-production development; homogeneous composition does not imply uniform gas or neutron distributions. Current deployment, economics and safety require separate evidence.",
        reviewed_on: "2026-10-01",
        source: "researchReactor aqueousSolutions",
      },
    ],
    [
      "Critical assembly",
      null,
      "deployed",
      "established",
      "A low-power assembly reaches criticality for reactor-physics measurements and core-configuration tests.",
      "Reactor-physics measurements and education",
      "Limited power; facility-specific reactivity control and licensing",
      "research configuration",
      {
        source: "researchReactor reactorDesign crocus crocusCourse",
        evidence_scope:
          "Low-power critical configuration, distinct from an assembly kept below criticality. EPFL CROCUS supplies a named teaching, measurement, control and licensing example; its operating limit and licence are not universal to all critical assemblies.",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Subcritical assembly",
      null,
      "deployed",
      "established",
      "A source-driven multiplying assembly operates below criticality using an external neutron source.",
      "Source-driven neutron multiplication while subcritical",
      "Subcriticality requires design-specific controls; source control alone does not establish safety",
      "research configuration",
      {
        source: "subcriticalAssembly",
        evidence_scope:
          "Established research configuration. IAEA-TECDOC-1976, section 2.1, printed page 3 (PDF page 13), distinguishes subcritical operation from an assembly's ability to reach criticality. Some assemblies rely on engineering and administrative provisions. This entry does not establish the safety of an individual design or exclude all reactivity excursions.",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Pulsed research reactor",
      null,
      "deployed",
      "established",
      "A research reactor produces short power pulses for neutron irradiation and experiments.",
      "High peak neutron output",
      "Transient control and design-specific fuel and safety limits",
      "operating mode",
      {
        source: "researchReactor reactorDesign researchAnalysis mainzMode",
        evidence_scope:
          "An operating-mode facet rather than a separate core geometry. Mainz provides a named pulse example; pulse capability, fuel feedback, peak power and permitted duration are design-specific and are not inherited by every research reactor.",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("fusion", "Toroidal magnetic confinement", "fusion rfp", [
    [
      "Tokamak",
      null,
      "research",
      "demonstrated",
      "External toroidal fields and a plasma current form confining helical magnetic field lines.",
      "Large experimental knowledge base",
      "Disruptions, power exhaust and sustained current drive",
      "architecture",
      { source: "fusion rfp fusionTechnology", reviewed_on: "2026-10-01" },
    ],
    [
      "Spherical tokamak",
      "Tokamak",
      "research",
      "demonstrated",
      "A low-aspect-ratio tokamak uses a compact central column.",
      "High plasma pressure relative to magnetic pressure",
      "Centre-column space and shielding for fusion-power designs",
      "subtype",
      { source: "fusion rfp stppPaper", reviewed_on: "2026-10-01" },
    ],
    [
      "Reversed-field pinch",
      null,
      "research",
      "demonstrated",
      "Toroidal magnetic field reverses direction near the edge of a current-carrying plasma.",
      "Relatively modest external toroidal field",
      "Magnetic relaxation and associated transport losses",
      "architecture",
      { source: "fusion rfp", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fusion", "Externally shaped toroidal confinement", "fusion helical", [
    [
      "Stellarator",
      null,
      "research",
      "demonstrated",
      "Three-dimensional external magnetic fields confine plasma without requiring large toroidal plasma current.",
      "Sustained-operation potential",
      "Complex coils, transport and exhaust",
      "architecture",
      { source: "fusion helical fusionTechnology", reviewed_on: "2026-10-01" },
    ],
    [
      "Heliotron / torsatron",
      "Stellarator",
      "research",
      "demonstrated",
      "Continuous helical coils create rotational transform around a toroidal plasma.",
      "Externally supplied confinement geometry",
      "Three-dimensional transport and engineering",
      "subtype",
      { source: "fusion helical fusionTechnology", reviewed_on: "2026-10-01" },
    ],
    [
      "Optimised modular stellarator",
      "Stellarator",
      "research",
      "demonstrated",
      "Individually shaped modular coils implement an optimised three-dimensional equilibrium.",
      "Optimisation can reduce neoclassical transport losses",
      "Coil tolerances and integrated reactor design",
      "subtype",
      {
        source: "fusion helical fusionTechnology w7xTransportPaper",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("fusion", "Open magnetic confinement", "fusion doeFusion", [
    [
      "Magnetic mirror",
      null,
      "research",
      "demonstrated",
      "Stronger magnetic fields at the ends reflect a portion of particle trajectories.",
      "Linear access and geometry",
      "Particle and heat losses through ends",
      "architecture",
      { source: "fusion doeFusion", reviewed_on: "2026-10-01" },
    ],
    [
      "Tandem mirror",
      "Magnetic mirror",
      "research",
      "demonstrated",
      "End cells create electrostatic potential barriers that improve axial confinement of the central mirror plasma.",
      "Potential reduction of axial losses",
      "End-cell heating and stability",
      "subtype",
      { source: "fusion doeFusion", reviewed_on: "2026-10-01" },
    ],
    [
      "Gas-dynamic mirror",
      "Magnetic mirror",
      "research",
      "demonstrated",
      "A long mirror trap has gas-dynamic end outflow when the effective loss-cone scattering mean free path is shorter than its length.",
      "Potential intense neutron-source applications",
      "End losses and heating requirements",
      "subtype",
      { source: "fusion doeFusion", reviewed_on: "2026-10-01" },
    ],
    [
      "Magnetic cusp confinement",
      null,
      "research",
      "research",
      "Opposing magnetic regions form cusp boundaries around the plasma.",
      "Favourable local curvature",
      "Losses through cusps",
      "architecture",
      { source: "fusion doeFusion", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fusion", "Dipole confinement", "dipole", [
    [
      "Levitated dipole",
      null,
      "research",
      "demonstrated",
      "Plasma surrounds a levitated magnetic dipole in a magnetosphere-like geometry.",
      "Inward particle redistribution and improved hot-electron stability in studied discharges",
      "Internal-coil neutron protection, cryogenic operation and reactor-scale validation",
      "architecture",
      { source: "dipole fusion ldxFinalReport", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fusion", "Compact toroids", "fusion spheromak", [
    [
      "Field-reversed configuration (FRC)",
      null,
      "research",
      "demonstrated",
      "A compact plasma has predominantly poloidal magnetic field with a reversed-field core.",
      "High beta and compact geometry",
      "Sustainment, particle losses and stability",
      "architecture",
      { source: "fusion spheromak", reviewed_on: "2026-10-01" },
    ],
    [
      "Spheromak",
      null,
      "research",
      "demonstrated",
      "Self-organised toroidal plasma carries both poloidal and toroidal magnetic fields.",
      "Simply connected confinement vessel without interlocking toroidal-field coils",
      "Relaxation, formation and sustained confinement",
      "architecture",
      { source: "fusion spheromak", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("fusion", "Pinch confinement", "fusion doeFusion dpf", [
    [
      "Z-pinch",
      null,
      "research",
      "demonstrated",
      "Axial plasma current creates an azimuthal magnetic field that compresses the column.",
      "Simple basic geometry",
      "Kink and sausage instabilities",
      "architecture",
      { source: "fusion doeFusion dpf", reviewed_on: "2026-10-01" },
    ],
    [
      "Sheared-flow-stabilised Z-pinch",
      "Z-pinch",
      "research",
      "demonstrated",
      "Velocity shear is used to suppress instability in a Z-pinch plasma.",
      "Reduced dependence on external confinement magnets",
      "Sustainment, electrode loads and scaling",
      "subtype",
      {
        source: "fusion doeFusion dpf shearFuZE2019 zPinchPerspective2020",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Theta pinch",
      null,
      "research",
      "demonstrated",
      "A changing axial magnetic field induces azimuthal current and compresses plasma.",
      "Rapid pulsed compression",
      "Axial losses and configuration-dependent plasma instabilities",
      "architecture",
      { source: "fusion doeFusion dpf", reviewed_on: "2026-10-01" },
    ],
    [
      "Dense plasma focus",
      null,
      "research",
      "demonstrated",
      "A pulsed discharge forms a transient dense pinched plasma region.",
      "Compact pulsed fusion-neutron production",
      "Repeatable neutron output, driver-to-radiation efficiency and electrode heat loads",
      "architecture",
      {
        source: "fusion doeFusion dpf densePlasmaDmp",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("fusion", "Inertial confinement", "fusion lle", [
    [
      "Laser direct-drive ICF",
      null,
      "research",
      "demonstrated",
      "Laser beams directly ablate and implode a fuel capsule.",
      "Direct energy coupling",
      "Illumination uniformity and hydrodynamic instability",
      "architecture",
      { source: "fusion lle", reviewed_on: "2026-10-01" },
    ],
    [
      "Laser indirect-drive ICF",
      null,
      "demonstrated",
      "demonstrated",
      "Laser energy heats an enclosure whose X-rays implode the fuel capsule.",
      "Experimentally demonstrated target ignition",
      "Driver-to-target efficiency and repetitive chambers",
      "architecture",
      { source: "fusion lle nifTargetGain2024", reviewed_on: "2026-10-01" },
    ],
    [
      "Fast-ignition ICF",
      null,
      "research",
      "research",
      "A separate short energy pulse is intended to ignite already compressed fuel.",
      "Separate compression and ignition optimisation",
      "Transporting ignition energy into the dense fuel",
      "ignition scheme",
      { source: "fusion lle", reviewed_on: "2026-10-01" },
    ],
    [
      "Shock-ignition ICF",
      null,
      "research",
      "research",
      "A strong late shock is designed to ignite compressed fuel.",
      "Potentially higher target gain from separate compression and ignition phases",
      "Shock timing and laser-plasma coupling",
      "ignition scheme",
      {
        source: "fusion lle shockPumpDepletion2019",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Heavy-ion-driven ICF",
      null,
      "concept",
      "research",
      "Accelerated heavy-ion beams provide the energy for target compression.",
      "Potential driver efficiency and repetition",
      "Beam focusing and integrated target performance",
      "architecture",
      { source: "fusion lle heavyIonDriver1988", reviewed_on: "2026-10-01" },
    ],
    [
      "Impact-driven inertial fusion",
      null,
      "research",
      "research",
      "A high-velocity projectile launches compression waves in a fusion target.",
      "Alternative energy driver",
      "Projectile velocity, integrity and target compression",
      "architecture",
      {
        source: "fusion lle impactFirstLight2022 impactIAEA2010",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("fusion", "Pulsed-power inertial fusion", "zicf maglif", [
    [
      "Z-pinch-driven indirect ICF",
      null,
      "concept",
      "research",
      "A pulsed-power Z-pinch supplies radiation to compress a separate fuel capsule.",
      "High pulsed-power energy delivery",
      "Radiation uniformity and hohlraum wall motion",
      "architecture",
      { source: "zicf maglif linerZDriver2000", reviewed_on: "2026-10-01" },
    ],
    [
      "MagLIF",
      null,
      "research",
      "demonstrated",
      "A metal liner compresses fuel that has been magnetised and preheated.",
      "Reduced thermal losses during compression",
      "Mix, liner stability and repetitive operation",
      "architecture",
      {
        source: "zicf maglif linerMagLIF2014 linerIAEA2022",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("fusion", "Magneto-inertial confinement", "mif pjif", [
    [
      "Solid-liner magnetised-target fusion",
      null,
      "research",
      "research",
      "An imploding solid liner compresses a magnetised plasma target.",
      "Intermediate density between magnetic and inertial schemes",
      "Liner contamination and replacement",
      "architecture",
      {
        source: "mif pjif linerIAEA2022 linerLM262026",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Liquid-liner magnetised-target fusion",
      null,
      "research",
      "research",
      "A driven liquid cavity compresses a magnetised plasma.",
      "Potential liquid neutron shielding",
      "Compression symmetry and plasma survival",
      "architecture",
      { source: "mif pjif linerIAEA2022", reviewed_on: "2026-10-01" },
    ],
    [
      "Plasma-jet-driven magneto-inertial fusion",
      null,
      "research",
      "research",
      "Converging plasma jets form a liner around a magnetised target.",
      "Stand-off drivers",
      "Jet merging, uniformity and energy coupling",
      "architecture",
      { source: "mif pjif linerPJMIF2018", reviewed_on: "2026-10-01" },
    ],
    [
      "Pulsed FRC compression",
      "Field-reversed configuration (FRC)",
      "research",
      "research",
      "A field-reversed plasma is rapidly compressed to increase density and temperature.",
      "Compact pulsed geometry",
      "Complete merging, formation-to-compression integration and plasma stability",
      "subtype",
      { source: "mif pjif frcHybrid2025", reviewed_on: "2026-10-01" },
    ],
  ]);
  add(
    "fusion",
    "Electrostatic and beam fusion",
    "iec polywell neutronGenerator",
    [
      [
        "Gridded inertial electrostatic confinement",
        null,
        "demonstrated",
        "demonstrated",
        "An electric potential accelerates ions through a transparent electrode structure.",
        "Established compact neutron-source principle",
        "Grid and recirculation losses",
        "architecture",
        {
          source: "iec polywell neutronGenerator iecJstage2018 ngIAEA2012",
          reviewed_on: "2026-10-01",
        },
      ],
      [
        "Polywell",
        null,
        "research",
        "research",
        "Magnetic cusps confine electrons intended to create an ion-accelerating electrostatic well.",
        "Potential reduction of ion escape through magnetic cusps",
        "Ion confinement and full power balance",
        "architecture",
        {
          source: "iec polywell neutronGenerator polywellOriginal2014",
          reviewed_on: "2026-10-01",
        },
      ],
      [
        "Accelerator beam-target fusion neutron generator",
        null,
        "deployed",
        "established",
        "A compact accelerator drives deuterium ions into a deuterium- or tritium-bearing target to produce D-D or D-T fusion neutrons.",
        "Switchable compact neutron production for research and industry",
        "Target loading, heat removal, tritium handling and poor energy efficiency",
        "device",
        {
          evidence_scope:
            "Established as a neutron source, not as an energy-producing concept. A beam-target generator consumes far more energy than it releases, because beam ions lose energy to scattering far faster than they fuse; no net-energy, gain or power claim is made or implied by this entry.",
          reviewed_on: "2026-09-29",
          source: "iec polywell neutronGenerator ngIAEA2012 dtGenerator2024",
        },
      ],
    ],
  );
  add("chemical", "Ideal flow and operating modes", "mit fogler", [
    [
      "Batch reactor",
      null,
      "deployed",
      "established",
      "Reactants are charged and react without continuous material throughput.",
      "Flexible campaigns",
      "Time-varying heat release in exothermic campaigns",
      "operating mode",
      {
        source: "mit fogler chemMitBatch chemHseIndg254 chemMitNonisothermal",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Semi-batch reactor",
      null,
      "deployed",
      "established",
      "One or more streams are added or withdrawn during a batch campaign.",
      "Controlled feed and heat release",
      "Accumulation and feed-interruption response",
      "operating mode",
      {
        source: "mit fogler chemMitBatch chemHseHsg143",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Continuous stirred-tank reactor (CSTR)",
      null,
      "deployed",
      "established",
      "The ideal well-mixed model has uniform vessel composition equal to its outlet.",
      "Mixing and controllability",
      "Back-mixing and possible multiple steady states under exothermic conditions",
      "architecture",
      {
        source:
          "mit fogler chemMitCstr chemMitRtd chemMitBatch chemMitNonisothermal",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Plug-flow / tubular reactor",
      null,
      "deployed",
      "established",
      "The ideal plug-flow model advances material along a tube without axial back-mixing.",
      "High conversion per volume in suitable kinetics",
      "Axial hot spots and pressure drop",
      "architecture",
      {
        source:
          "mit fogler chemMitPfr chemMitRtd chemMitSeries chemMitNonisothermal",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "CSTR cascade",
      "Continuous stirred-tank reactor (CSTR)",
      "deployed",
      "established",
      "Multiple mixed vessels in series shape the residence-time distribution.",
      "Options for staged feeds and stage temperatures; benefits depend on kinetics.",
      "Additional equipment and coupled dynamics",
      "configuration",
      {
        source:
          "mit fogler chemMitRtd chemMitCstr chemSquStepFeed chemImaReactiveCrystallisation chemBuffaloNetworks chemUowTwoCstrAbstract",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("chemical", "Catalytic and multiphase reactors", "mit slurry fogler", [
    [
      "Fixed / packed-bed reactor",
      null,
      "deployed",
      "established",
      "Fluid passes through stationary catalyst or reactive solid particles.",
      "High catalyst loading for slow reactions without dominant transport limits",
      "Pressure drop and heat gradients",
      "architecture",
      {
        source:
          "mit slurry fogler multiMitPorousPacked multiOstimovingAttrition multiQubSlurryChapter multiFoglerLaboratory",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Moving-bed reactor",
      null,
      "deployed",
      "established",
      "Solid reactant or catalyst moves through the reaction zone.",
      "Continuous solids replenishment",
      "Solids distribution and attrition",
      "architecture",
      {
        source:
          "mit slurry fogler multiUopCcr multiNetlMovingModel multiOstimovingAttrition",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Bubbling fluidised-bed reactor",
      null,
      "deployed",
      "established",
      "Upward fluid flow suspends solids in a bubbling bed.",
      "Strong heat transfer",
      "Bubble bypassing and entrainment",
      "architecture",
      {
        source:
          "mit slurry fogler multiFoglerFluidised multiNptelFluidisedHeat multiNptelFluidisedFaq",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Circulating fluidised-bed reactor",
      null,
      "deployed",
      "established",
      "Entrained solids circulate between reaction and separation zones.",
      "Continuous solids recirculation for repeated gas-solid contact",
      "Erosion and solids separation",
      "architecture",
      {
        source:
          "mit slurry fogler multiNetlCirculatingOxygen multiNptelFluidisedFaq",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Trickle-bed reactor",
      null,
      "deployed",
      "established",
      "Gas and liquid flow through a fixed bed of catalyst.",
      "Established gas-liquid catalytic processing",
      "Incomplete wetting and transport limits",
      "architecture",
      {
        source:
          "mit slurry fogler multiFoglerTrickle multiPurdueTrickleAbstract",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Slurry stirred-tank reactor",
      null,
      "deployed",
      "established",
      "Catalyst particles are suspended in a mechanically agitated liquid.",
      "Good temperature control",
      "Catalyst recovery and gas transfer",
      "architecture",
      {
        source:
          "mit slurry fogler multiFoglerLaboratory multiFoglerSlurry multiPittSlurryScale",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Bubble-column reactor",
      null,
      "deployed",
      "established",
      "Rising gas bubbles provide contact and mixing in a liquid column.",
      "Simple gas-driven mixing configuration",
      "Flow-regime transitions and scale-up",
      "architecture",
      {
        source: "mit slurry fogler multiBubbleExperimental multiNptelAirDriven",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Airlift reactor",
      "Bubble-column reactor",
      "deployed",
      "established",
      "Different gas holdup in riser and downcomer drives liquid circulation.",
      "Relatively low-shear circulation; stress rises with aeration",
      "Gas transfer and geometric scale-up",
      "subtype",
      {
        source:
          "mit slurry fogler multiDtuAirliftExperiments multiAirliftHydrodynamics",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add(
    "chemical",
    "Membrane and flow intensification",
    "membrane micro fogler",
    [
      [
        "Catalytic membrane reactor",
        null,
        "demonstrated",
        "demonstrated",
        "A catalytic reactor couples reaction with selective transport through a membrane.",
        "Coupled separation and reaction",
        "Membrane selectivity and stability under reaction conditions",
        "architecture",
        { source: "membrane", reviewed_on: "2026-10-01" },
      ],
      [
        "Microchannel flow reactor",
        null,
        "deployed",
        "established",
        "Small channels shorten transport distances and increase surface area relative to volume.",
        "Rapid heat and mass transfer with suitable mixing geometry",
        "Clogging and flow distribution during numbering-up",
        "architecture",
        { source: "micro flowNumbering", reviewed_on: "2026-10-01" },
      ],
      [
        "Segmented-flow reactor",
        null,
        "demonstrated",
        "demonstrated",
        "Immiscible gas or liquid phases form alternating slugs or droplets in a channel.",
        "Small reaction compartments with controlled residence time",
        "Phase separation and flow control during scale-out",
        "configuration",
        {
          source: "flowGasSlug flowSftr flowNumbering",
          reviewed_on: "2026-10-01",
        },
      ],
    ],
  );
  add("chemical", "Electrolysis", "electrolyzer fuelcell", [
    [
      "Alkaline water electrolyser",
      null,
      "deployed",
      "established",
      "Electrodes split water in an alkaline electrolyte separated by a diaphragm.",
      "Established materials and deployment",
      "Gas crossover and dynamic operating range",
      "architecture",
      { source: "electrolyzer doeElectrolysis", reviewed_on: "2026-10-01" },
    ],
    [
      "PEM water electrolyser",
      null,
      "deployed",
      "established",
      "A proton-exchange membrane transports ions between water-splitting electrodes.",
      "Compact high-current operation",
      "Catalyst cost and membrane lifetime",
      "architecture",
      { source: "electrolyzer doeElectrolysis", reviewed_on: "2026-10-01" },
    ],
    [
      "Solid-oxide electrolyser",
      null,
      "demonstrated",
      "demonstrated",
      "A ceramic electrolyte enables high-temperature steam or carbon-dioxide electrolysis.",
      "Heat-assisted electrical efficiency",
      "Thermal cycling and degradation",
      "architecture",
      {
        source: "electrolyzer doeElectrolysis pnnlSyngas",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Anion-exchange-membrane electrolyser",
      null,
      "research",
      "research",
      "A polymer membrane transports hydroxide ions in an alkaline electrolysis cell.",
      "Potential reduced precious-metal dependence",
      "Membrane and electrode durability",
      "architecture",
      { source: "electrolyzer doeElectrolysis", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("chemical", "Fuel-cell reactors", "fuelcell", [
    [
      "PEM fuel cell",
      null,
      "deployed",
      "established",
      "A proton-conducting membrane supports electrochemical fuel oxidation and oxygen reduction.",
      "Responsive low-temperature operation",
      "Fuel purity, catalysts and water management",
      "architecture",
      { source: "fuelcell fuelCellTypes", reviewed_on: "2026-10-01" },
    ],
    [
      "Alkaline fuel cell",
      null,
      "deployed",
      "established",
      "Hydroxide-conducting electrolyte couples fuel and oxygen electrode reactions.",
      "Favourable electrode kinetics",
      "Carbon-dioxide sensitivity",
      "architecture",
      { source: "fuelcell fuelCellTypes", reviewed_on: "2026-10-01" },
    ],
    [
      "Phosphoric-acid fuel cell",
      null,
      "deployed",
      "established",
      "A phosphoric-acid electrolyte supports medium-temperature electrochemical conversion.",
      "Stationary combined heat and power experience",
      "Catalyst loading and electrolyte management",
      "architecture",
      { source: "fuelcell fuelCellTypes", reviewed_on: "2026-10-01" },
    ],
    [
      "Molten-carbonate fuel cell",
      null,
      "deployed",
      "established",
      "Carbonate ions carry charge through a molten electrolyte.",
      "High-temperature fuel flexibility",
      "Corrosion and carbon-dioxide balance",
      "architecture",
      { source: "fuelcell fuelCellTypes", reviewed_on: "2026-10-01" },
    ],
    [
      "Solid-oxide fuel cell",
      null,
      "deployed",
      "established",
      "A ceramic electrolyte supports high-temperature electrochemical fuel conversion.",
      "Fuel flexibility and useful heat",
      "Thermal stress and long-term degradation",
      "architecture",
      { source: "fuelcell fuelCellTypes", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("chemical", "Photochemical reactors", "photo", [
    [
      "Homogeneous photochemical flow reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Light activates dissolved reagents or catalysts in an illuminated flow path.",
      "Short optical paths for illuminating the reaction mixture",
      "Light penetration and photochemical scale-up",
      "architecture",
      { source: "flowNumbering", reviewed_on: "2026-10-01" },
    ],
    [
      "Slurry photocatalytic reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Suspended photocatalyst particles absorb light while contacting the fluid.",
      "Short diffusion distances to well-dispersed catalyst",
      "Scattering and catalyst separation",
      "architecture",
      { source: "photo", reviewed_on: "2026-10-01" },
    ],
    [
      "Immobilised photocatalytic reactor",
      null,
      "demonstrated",
      "demonstrated",
      "A fixed photocatalyst coating reacts with illuminated flowing fluid.",
      "Simpler catalyst retention",
      "Mass transfer and illuminated area",
      "architecture",
      { source: "photo", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("chemical", "Plasma chemistry", "plasma", [
    [
      "Dielectric-barrier-discharge reactor",
      null,
      "deployed",
      "established",
      "A dielectric barrier controls electrical discharges through a gas.",
      "Non-thermal gas activation",
      "Energy efficiency and discharge uniformity",
      "architecture",
      {
        source: "plasmaHydrogenation plasmaTechnoeconomic",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Microwave plasma reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Microwave energy sustains a reactive plasma.",
      "Electrodeless energy coupling",
      "Coupling efficiency and thermal management",
      "architecture",
      {
        source: "plasmaMicrowaveProtocol plasmaTechnoeconomic",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Gliding-arc plasma reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Gas flow stretches a moving arc discharge through the reaction region.",
      "Reactive chemistry at intermediate thermal conditions",
      "Electrode wear and reaction recombination",
      "architecture",
      {
        source:
          "plasmaGlidingDiagnostics plasmaGlidingExperiment plasmaTechnoeconomic",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Thermal plasma / arc reactor",
      null,
      "deployed",
      "established",
      "An electrical arc generates high-temperature gas for chemical or material conversion.",
      "High-temperature material conversion",
      "Electricity demand and refractory thermal loads",
      "architecture",
      {
        source: "plasmaHydrogenation plasmaThermalNetl",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("chemical", "Polymerisation", "polymer", [
    [
      "Bulk polymerisation reactor",
      null,
      "deployed",
      "established",
      "Monomer polymerises with little or no solvent.",
      "High polymer concentration",
      "Viscosity growth and heat removal",
      "process class",
      {
        source: "polymerNptelTechnology polymerNptelProcesses",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Solution polymerisation reactor",
      null,
      "deployed",
      "established",
      "A solvent carries monomer and polymer through the reaction.",
      "Heat removal and viscosity control",
      "Solvent recovery",
      "process class",
      {
        source: "polymerNptelTechnology polymerNptelProcesses",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Suspension polymerisation reactor",
      null,
      "deployed",
      "established",
      "Monomer droplets polymerise while dispersed in a continuous phase.",
      "Bead formation and heat transfer",
      "Droplet stability and fouling",
      "process class",
      {
        source:
          "polymerNptelTechnology polymerDispersedTutorial polymerNptelProcesses",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Emulsion polymerisation reactor",
      null,
      "deployed",
      "established",
      "Polymer particles grow in a stabilised dispersed system.",
      "Potential for high rates and low bulk viscosity",
      "Particle-size control and residual ingredients",
      "process class",
      {
        source:
          "polymerNptelEmulsion polymerDispersedTutorial polymerEmulsionMonitoring",
        reviewed_on: "2026-10-01",
      },
    ],
  ]);
  add("chemical", "Thermochemical conversion", "gasifier pyro hydro", [
    [
      "Moving / fixed-bed gasifier",
      null,
      "deployed",
      "established",
      "Solid feed passes through drying, pyrolysis and gasification regions in a bed.",
      "Coarse-feed compatibility",
      "Tar formation and feed-size constraints",
      "architecture",
      {
        source: "thermoNetlHandbook thermoNetlWagner thermoNetlTypes",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Fluidised-bed gasifier",
      null,
      "deployed",
      "established",
      "Fluidised solids contact gasifying agents at relatively uniform temperature.",
      "Feed flexibility with suitable preparation",
      "Agglomeration and solids separation",
      "architecture",
      { source: "thermoNetlTypes thermoNetlWagner", reviewed_on: "2026-10-01" },
    ],
    [
      "Entrained-flow gasifier",
      null,
      "deployed",
      "established",
      "Fine particles or droplets react while entrained in a high-temperature flow.",
      "Potential for high conversion and low tar",
      "Feed preparation and slag handling",
      "architecture",
      {
        source: "thermoNetlTypes thermoNetlWagner thermoNetlHandbook",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Fast-pyrolysis reactor",
      null,
      "demonstrated",
      "demonstrated",
      "Rapid heating without added oxygen converts feed into vapours, gases and char.",
      "Liquid-product potential",
      "Rapid vapour quenching and product stability",
      "process class",
      {
        source: "thermoNrelTcpdu thermoPyrolysisExperiment thermoNrelAging",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Supercritical-water gasification reactor",
      null,
      "research",
      "demonstrated",
      "Wet feed reacts in water above its critical point.",
      "Wet-feed conversion without preliminary drying",
      "Salt deposition, corrosion and pressure containment",
      "architecture",
      { source: "thermoScwgRetained", reviewed_on: "2026-10-01" },
    ],
  ]);
  add(
    "chemical",
    "Coupled redox and treatment cycles",
    "chemicalLooping sequencingBatch",
    [
      [
        "Chemical-looping reactor system",
        null,
        "demonstrated",
        "demonstrated",
        "A solid oxygen carrier cycles between coupled fuel and air reactors.",
        "Separate air and fuel-product streams through oxygen-carrier redox cycling",
        "Carrier durability, solids circulation and scale-up",
        "coupled reactor architecture",
        { source: "chemicalLooping", reviewed_on: "2026-10-01" },
      ],
      [
        "Sequencing batch reactor",
        null,
        "deployed",
        "established",
        "A wastewater-treatment basin cycles through fill, react, settle, draw and idle phases.",
        "Time-phased treatment in one vessel",
        "Cycle control and variable loading",
        "operating configuration",
        { source: "sequencingBatch", reviewed_on: "2026-10-01" },
      ],
    ],
  );
  add("chemical", "Biochemical culture systems", "bio mit", [
    [
      "Stirred-tank fermenter",
      null,
      "deployed",
      "established",
      "Mechanical agitation mixes microbial or cell cultures in a monitored vessel.",
      "Adjustable agitation and monitoring of culture conditions",
      "Oxygen transfer, shear and sterility",
      "architecture",
      {
        source:
          "cultureBioStemCellStirred cultureBioPerfusionExperiment cultureMitOxygenTransfer",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Fed-batch bioreactor",
      null,
      "deployed",
      "established",
      "Nutrients are added during cultivation without matching continuous product outflow.",
      "Feed-controlled growth with reduced substrate overload",
      "Feed strategy and changing volume",
      "operating mode",
      { source: "cultureMitChemostatFedBatch", reviewed_on: "2026-10-01" },
    ],
    [
      "Chemostat",
      null,
      "deployed",
      "established",
      "Continuous nutrient feed and matching outflow can sustain a microbial steady state.",
      "Reproducible culture conditions at steady state",
      "Washout and contamination",
      "operating mode",
      {
        source:
          "cultureBioChemostatProtocol cultureMitChemostatFedBatch cultureBioChemostatSterility",
        reviewed_on: "2026-10-01",
      },
    ],
    [
      "Cell-retention / perfusion bioreactor",
      null,
      "deployed",
      "established",
      "Fresh medium and product are exchanged while cells are retained.",
      "High cell density with effective retention and nutrient supply",
      "Retention-device reliability, filter fouling and flow control",
      "operating mode",
      { source: "cultureBioPerfusionExperiment", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("chemical", "Anaerobic digestion", "digester wastewater", [
    [
      "Complete-mix anaerobic digester",
      null,
      "deployed",
      "established",
      "A mixed vessel supports oxygen-free microbial conversion of organic feed.",
      "Mixing promotes more uniform bulk conditions",
      "Biological stability and mixing demand",
      "architecture",
      { source: "adOperator adDesign", reviewed_on: "2026-10-01" },
    ],
    [
      "Plug-flow anaerobic digester",
      null,
      "deployed",
      "established",
      "Organic slurry passes through an elongated anaerobic vessel.",
      "Suitable for relatively high-solids manure slurry",
      "Solids accumulation and clean-out requirements",
      "architecture",
      { source: "digester adDesign", reviewed_on: "2026-10-01" },
    ],
    [
      "Covered anaerobic lagoon",
      null,
      "deployed",
      "established",
      "A covered lagoon captures gas from anaerobic treatment of dilute organic wastes.",
      "Simple large-volume treatment",
      "Climate sensitivity and large footprint",
      "architecture",
      { source: "digester adDesign", reviewed_on: "2026-10-01" },
    ],
    [
      "Upflow anaerobic sludge-blanket reactor",
      null,
      "deployed",
      "established",
      "Wastewater rises through a dense anaerobic granular-sludge bed that retains active biomass.",
      "High biomass retention without packing",
      "Granule formation, hydraulics and effluent polishing",
      "architecture",
      { source: "adUasb wastewater", reviewed_on: "2026-10-01" },
    ],
    [
      "Fixed-film anaerobic reactor",
      null,
      "deployed",
      "established",
      "Anaerobic microorganisms grow on support media while wastewater flows through the reactor.",
      "Biomass retention with relatively compact treatment",
      "Media clogging and influent solids removal",
      "architecture",
      { source: "digester adDesign", reviewed_on: "2026-10-01" },
    ],
  ]);
  add("hybrid", "Fusion-fission coupling", "hybrid", [
    [
      "Fusion-fission hybrid energy multiplier",
      null,
      "concept",
      "research",
      "Fusion-source neutrons drive energy-producing fission in a surrounding blanket.",
      "Neutron multiplication",
      "Integration of fusion and fission engineering",
      "architecture",
      { source: "hybridDOE2009", reviewed_on: "2026-10-02" },
    ],
    [
      "Fusion-driven transmutation system",
      null,
      "concept",
      "research",
      "A fusion neutron source drives reactions in selected long-lived nuclear materials.",
      "Potential specialised fuel-cycle service",
      "Fuel fabrication, separations and driver availability",
      "application architecture",
      { source: "hybridDOE2009", reviewed_on: "2026-10-02" },
    ],
    [
      "Fusion-fission breeder",
      null,
      "concept",
      "research",
      "Fusion neutrons support fissile breeding in fertile blanket material.",
      "Potential fuel production",
      "Fuel-cycle integration and material accounting",
      "application architecture",
      { source: "hybridDOE2009", reviewed_on: "2026-10-02" },
    ],
  ]);
  add("hybrid", "Accelerator-fission coupling", "ads", [
    [
      "Accelerator-driven subcritical system (ADS)",
      null,
      "research",
      "demonstrated",
      "Accelerator-generated neutrons sustain fission in a subcritical assembly.",
      "Source-controlled neutron supply",
      "Accelerator reliability and target durability",
      "architecture",
      { source: "ads hybridADS2015", reviewed_on: "2026-10-02" },
    ],
  ]);
  add("hybrid", "Integrated energy systems", "integrated", [
    [
      "Nuclear-renewable hybrid energy system",
      null,
      "research",
      "research",
      "Nuclear heat or electricity is coordinated with renewables and conversion processes.",
      "Flexible energy services",
      "Integrated control and market-dependent economics",
      "system integration",
      { source: "integrated hybridNR2022", reviewed_on: "2026-10-02" },
    ],
    [
      "Nuclear heat coupled to hydrogen production",
      null,
      "research",
      "research",
      "Nuclear heat and electricity support electrolysis or thermochemical hydrogen processes.",
      "Low-carbon process-energy supply",
      "Heat interfaces and coupled plant qualification",
      "system integration",
      { source: "integrated hybridH2024", reviewed_on: "2026-10-02" },
    ],
  ]);
  add(
    "hybrid",
    "Externally driven low-temperature fusion",
    "muon lattice beam pyroFusion",
    [
      [
        "Muon-catalysed fusion",
        null,
        "demonstrated",
        "demonstrated",
        "Muons form compact molecular states that permit hydrogen-isotope fusion at low bulk temperature.",
        "Well-established nuclear reaction mechanism",
        "Muon production cost and muon sticking",
        "architecture",
        {
          source: "muon lattice beam pyroFusion lowMuon2007",
          reviewed_on: "2026-10-02",
        },
      ],
      [
        "Lattice-confinement fusion",
        null,
        "research",
        "research",
        "External radiation or particles initiate nuclear reactions in deuterium-loaded materials.",
        "Dense solid-target fuel inventory",
        "Further validating fusion-neutron spectra and resolving higher-energy neutron sources",
        "architecture",
        {
          source:
            "muon lattice beam pyroFusion lowLatticeTheory2020 lowLatticeExperiment2020",
          reviewed_on: "2026-10-02",
        },
      ],
      [
        "Electrochemically loaded beam-target fusion",
        null,
        "research",
        "demonstrated",
        "Electrochemical loading changes a metal target bombarded by energetic deuterium ions.",
        "Controllable target loading",
        "Beam power greatly exceeds fusion output",
        "architecture",
        {
          source: "muon lattice beam pyroFusion lowBeam2025",
          reviewed_on: "2026-10-02",
        },
      ],
      [
        "Pyroelectric fusion source",
        null,
        "demonstrated",
        "demonstrated",
        "Temperature changes in a crystal generate an ion-accelerating electric field.",
        "Compact pulsed nuclear-reaction source",
        "Very low yield and external energy input",
        "architecture",
        {
          source: "muon lattice beam pyroFusion lowPyro2005",
          reviewed_on: "2026-10-02",
        },
      ],
    ],
  );
  add("hybrid", "Contested nuclear claims", "lenr callisto", [
    [
      "Palladium-deuterium electrochemical LENR",
      null,
      "contested",
      "contested",
      "Reports attribute anomalous heat or nuclear products to electrochemically loaded palladium.",
      "Testable calorimetric and nuclear-product claims",
      "Replication failures and inconsistent product accounting",
      "architecture",
      {
        source:
          "lenr callisto contestedGoogle2019 contestedDOE1989 contestedCallistoElectrochemical",
      },
    ],
    [
      "Gas-loaded metal-hydrogen LENR",
      null,
      "contested",
      "contested",
      "Reports attribute excess heat to hydrogen-isotope loading of metals under chemical conditions.",
      "Testable material and heat-balance claims",
      "Reproducibility and comprehensive energy accounting",
      "architecture",
      { source: "lenr callisto contestedGoogle2019 contestedCallistoPressure" },
    ],
  ]);
  add("hybrid", "Contested acoustic nuclear claims", "bubble", [
    [
      "Cavitation / bubble fusion",
      null,
      "contested",
      "contested",
      "Claims propose nuclear reactions during the collapse of acoustically driven bubbles.",
      "A falsifiable claimed nuclear signature",
      "Failed replication of key neutron claims",
      "architecture",
      { source: "bubble contestedCavitation2012 contestedShapira2002" },
    ],
  ]);
  add(
    "hybrid",
    "Space nuclear and speculative propulsion",
    "ntr fragment antimatter dfd",
    [
      [
        "Solid-core nuclear thermal rocket",
        null,
        "demonstrated",
        "demonstrated",
        "A fission reactor heats propellant that expands through a nozzle.",
        "Ground-tested nuclear propulsion principle",
        "Fuel endurance and flight qualification",
        "application architecture",
        { source: "ntr fragment antimatter dfd propulsionRover1991" },
      ],
      [
        "Fission-fragment propulsion reactor",
        null,
        "concept",
        "concept",
        "Escaping energetic fission fragments are proposed as direct exhaust.",
        "High theoretical exhaust velocity",
        "Fragment escape, criticality and heat rejection",
        "architecture",
        {
          source:
            "ntr fragment antimatter dfd propulsionFFREAbstract2014 propulsionFFRE2012",
        },
      ],
      [
        "Antiproton-catalysed microfission / fusion",
        null,
        "concept",
        "concept",
        "Antiprotons are proposed to trigger nuclear-energy release in small fuel targets.",
        "Theoretical compact ignition source",
        "Antimatter production, storage and delivery",
        "architecture",
        {
          source:
            "ntr fragment antimatter dfd propulsionAntiproton1994 propulsionHiPAT2000",
        },
      ],
      [
        "Direct fusion drive",
        "Field-reversed configuration (FRC)",
        "concept",
        "research",
        "A proposed compact fusion system couples power production to heated propellant exhaust.",
        "Combined propulsion and onboard power",
        "Fusion-core performance remains unproven",
        "application architecture",
        { source: "ntr fragment antimatter dfd propulsionDFD2019" },
      ],
    ],
  );
  add(
    "hybrid",
    "Chemical energy integration",
    "solar plasmaCatalysis artificial",
    [
      [
        "Solar thermochemical redox reactor",
        null,
        "demonstrated",
        "demonstrated",
        "Concentrated solar heat cycles reactive oxides to convert water or carbon dioxide.",
        "Direct solar-to-chemical energy storage",
        "Heat recovery and cyclic material durability",
        "architecture",
        { source: "solar plasmaCatalysis artificial solarTower2022" },
      ],
      [
        "Plasma-catalytic reactor",
        null,
        "research",
        "demonstrated",
        "A plasma and catalyst jointly influence reaction pathways.",
        "Electrified activation and selectivity research",
        "Energy yield and reproducible synergy",
        "architecture",
        { source: "solar plasmaCatalysis artificial plasmaMehta2020" },
      ],
      [
        "Photovoltaic-photothermal artificial photosynthesis",
        null,
        "research",
        "research",
        "Coupled electrical and thermal solar stages drive chemical transformations.",
        "Complementary solar-energy conversion routes",
        "Durability and full-system energy accounting",
        "system integration",
        { source: "solar plasmaCatalysis artificial pvPhotosynthesisV1" },
      ],
    ],
  );
  add("hybrid", "Bioelectrochemical systems", "mfc mec", [
    [
      "Microbial fuel cell",
      null,
      "research",
      "demonstrated",
      "Microorganisms transfer electrons from substrate oxidation to an external circuit.",
      "Combined treatment and electrical recovery",
      "Low power density and scale-up",
      "architecture",
      { source: "mfc mec mfcReview2022" },
    ],
    [
      "Microbial electrolysis cell",
      null,
      "research",
      "demonstrated",
      "Microbial oxidation and applied voltage jointly support product-forming electrode reactions.",
      "Waste-stream valorisation",
      "Catalyst poisoning and full-system energy accounting",
      "architecture",
      { source: "mfc mec mecCathode2021" },
    ],
  ]);
  const rows = builder.complete();
  window.REACTOR_TAXONOMY = rows;
  window.REACTOR_TAXONOMY_SOURCES = sources;
  window.REACTOR_TAXONOMY_META = {
    snapshot: "2026-09-26",
    version: 2,
    count_definition:
      "Indexed architectures, subtypes, operating modes and integration concepts; categories overlap.",
    completeness:
      "Expanded working taxonomy, not exhaustive. Facility, fuel, vendor and power-size facets require separate linked registries.",
    limitations: [
      "No claim that a listed concept has generated net electricity.",
      "Source links include reviews, developer papers and conceptual studies; evidence labels must be read with evidence_scope.",
      "Deployment and readiness refer to the family, not every proposed implementation.",
      "Chemical process modes may combine in a single reactor.",
      "Combustion variants, additional bioreactor geometries and historical concepts need deeper expansion.",
      "Scale and control scores were removed because no common validated cross-domain scoring rubric exists.",
    ],
  };
})();

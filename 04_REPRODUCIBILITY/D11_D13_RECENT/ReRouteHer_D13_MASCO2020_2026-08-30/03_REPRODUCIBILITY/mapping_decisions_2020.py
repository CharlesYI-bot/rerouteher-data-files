"""2020-specific project decisions after fresh title/profile retrieval.

Keys are MASCO 2020 six-digit codes, never current-portal code positions.
Relations describe approximate occupational scope, not government equivalence.
"""
DECISIONS={}
def add(codes,esco,relation,reason):
    for code in codes.split():
        assert code not in DECISIONS,code
        DECISIONS[code]={'code':esco,'relation':relation,'rationale':reason}

add('121104','1211.1.3','close_match','Budget Manager has its own exact preferred ESCO occupation. Replace the inherited financial-accounting proxy.')
add('121109','2412.7','close_match','Fund Manager is an alternate label for investment fund manager; portfolio/fund duties support the same function.')
add('121411','1324.8','close_match','The separated 2020 Supply Chain Manager matches the preferred ESCO title; no longer share its profile indiscriminately with logistics management.')
add('131202','1312.3','partial_proxy','Fishery production management retains an aquaculture-production proxy for testing. Capture fisheries and aquaculture are not exact equivalents; production management is closer in level than a fish-processing operator.')
add('131203','1312.3','close_match','The separated Aquaculture Production Manager is an exact preferred ESCO occupation.')
add('132102','1321.2.1','close_match','Manufacturing production-and-operation management corresponds to industrial production management in the compared profiles.')
add('132405','1324.3','close_match','Logistics Manager is an ESCO alternate title and the duties concern storage, distribution and transport. Replace the shared supply-chain-manager assignment for this 2020 split.')
add('132414','1324.3','broader_proxy','Shipping Manager oversees cargo movement, logistics schedules and distribution. The logistics/distribution manager preserves management level better than the inherited port-coordinator role; maritime-specific scope remains unrepresented.')
add('151101','1330.2','close_match','Chief Information Officer is the separated 2020 identity and an exact ESCO preferred title.')
add('151102','1330.1','close_match','Chief Data Officer is a separate preferred ESCO occupation. Replace the inherited Chief Information Officer assignment.')
add('151103','2529.1','close_match','Chief Information Security Officer is an alternate label of Chief ICT Security Officer; use the security leadership occupation rather than Chief Information Officer.')
add('151108','1330.5','partial_proxy','The inherited community-centre profile concerns ICT infrastructure and digital services. ICT operations management covers that component, not all community-centre or social-development responsibilities.')
add('151112 151135','1330.5.1','close_match','The 2020 application/software development management identity concerns coordinating software teams and delivery; Software Manager is the functional ESCO counterpart.')
add('151113','1330.5','broader_proxy','Data Operations Manager runs data infrastructure, workflows and service operations. Use ICT Operations Manager rather than assuming enterprise-wide Chief Data Officer authority; data-governance specialization remains incomplete.')
add('151117','1330.5','broader_proxy','Network Manager directs services and infrastructure. Reject the operational Network Administrator alias as automatic equivalence because management authority differs; retain the broader ICT operations management profile.')
add('151123','1330.5','broader_proxy','Information Technology Infrastructure Manager concerns infrastructure resources and daily ICT operations. The broader ICT operations management profile is retained with its scope caveat.')
add('161202','2221.2','partial_proxy','Director, Nursing has leadership and policy duties beyond the ESCO general-care nurse profile. The nursing-care proxy supports a test but is not a director-level equivalence.')
add('212106','2120.6','close_match','Applied Statistics is a statistician specialization; statistical analysis and reporting duties support the general ESCO Statistician occupation.')
add('212112 212113','2120.1','broader_proxy','Pricing/Valuation Actuarie is the printed 2020 spelling. Retain the actuarial-consultant umbrella; pricing versus valuation/reserving specialties are not separately covered. Do not select property valuation or generic product pricing by word overlap.')
add('213169','6112.1','close_match','Arborist is an alternate label of Arboriculturist; tree cultivation and health management fit. The narrower tree-surgery alternative is not chosen automatically.')
add('213306','2131.4.6.1','partial_proxy','The separated Horticulturist includes plant collections, botanical gardens and landscapes. Curator of Horticulture is a reviewed partial professional-profile proxy; generic horticulture is not identical to botanical-curator seniority or scope.')
add('214413','2144.1.5','broader_proxy','Internal Combustion Engine Engineer designs, installs and maintains engines. Engine Designer is more focused than the inherited general mechanical-engineer profile, but includes engine types beyond internal combustion.')
add('214649','2146.3','broader_proxy','Blasting Expert concerns mining explosives and controlled blasting. Explosives Engineer is retained as a broader engineering proxy, not abrasive surface blasting or bomb disposal.')
add('221101 221120','2211.1','close_match','Medical Officer UD41/UD43 denotes clinical medical practice in the inherited duties. General Practitioner is the clinical counterpart; the public-service grade does not imply health-and-safety or police work.')
add('226324','3257.5','partial_proxy','Authorised Gas Tester assesses workplace atmospheric hazards. Occupational Health and Safety Inspector covers part of the safety inspection function; gas-service installation and engine testing are different occupations.')
add('226325','2133.14','partial_proxy','Indoor Air Quality Assessor samples and analyses airborne contamination and recommends controls. Air Pollution Analyst provides a focused partial profile; indoor workplace and Malaysian assessor certification requirements remain local.')
add('226327','3257.5','broader_proxy','Chemical Assessor evaluates workplace chemical exposure and hazards. Occupational safety inspection is a broader proxy; product chemical testing alone does not establish occupational exposure assessment.')
add('226901','2269.8','close_match','X-Ray Technician U41 has patient imaging and radiography duties. Radiographer is the appropriate clinical occupation, not radio equipment service or general nuclear-plant work.')
add('238103 238106 238107 238108','2320.1','broader_proxy','Assistant vocational-training officer grades share instructional duties. Vocational Teacher supplies a broader test profile; assistant status, subject specialty and Malaysian grades are not represented.')
add('243114','2433.6','broader_proxy','Trade Product Specialist demonstrates technical products and supports customers and sales. Retain the technical sales representative profile; product-manager or advertising-specialist authority is not inferred.')
add('252108','2521.1','broader_proxy','Oracle Database Specialist performs administration and maintenance. Database Administrator is the broader vendor-neutral counterpart; no Oracle-specific skill completeness is claimed.')
add('252411','2511.11','close_match','Machine Learning Engineer is an ESCO alternate label of Artificial Intelligence Engineer and fits the compared engineering duties.')
add('252413','2511.11','close_match','Artificial Intelligence Engineer (AI) matches the ESCO preferred occupation after the explanatory acronym; this is no longer only a combined-role inheritance.')
add('254120','2166.5','broader_proxy','The separated Multimedia Artist produces digital visual artwork across media. Digital Artist is the broader artistic profile; specialist animation and media-production skills may be incomplete.')
add('254206','2166.1','partial_proxy','3D Artist is an ESCO alternate label of 3D Modeller. Modelling covers only part of the inherited generalist role, which also includes lighting, animation and effects; retain partial status.')
add('254211','2654.1','close_match','Art director is now the precise 2020 identity. Its visual-layout and artistic-team duties match ESCO Art Director, replacing the inherited Creative Director profile.')
add('254305','2166.7','broader_proxy','Multimedia Designer creates visual and interactive media. Digital Media Designer is a broader cross-media counterpart; no automatic restriction to web design is made.')
add('282407','2634.2.4','close_match','Psychotherapist is an exact ESCO preferred occupation and the inherited mental-health treatment description supports it.')
add('311125','3111.8','broader_proxy','Climate Service Technician supports weather/climate measurement and data. Meteorology Technician is the broader functional counterpart, not heating-system service.')
add('311516 311517','4323.11','partial_proxy','Dry/graving-dock dockmasters coordinate docking operations. Port Coordinator is retained as a partial maritime-operations proxy; dock safety, repair-yard authority and dry-dock plant duties are not fully represented.')
add('311531 311552','3257.5','partial_proxy','Hygiene Technician 1/2 retains a workplace-exposure/safety inspection proxy. The source profile mixes competent-person hygiene assessment with routine cleaning; preserve that source-quality warning and do not map to dental or sterile-services work.')
add('311544','3118.3.5','broader_proxy','AutoCAD drafting is technical CAD work. Mechanical Engineering Drafter is a broader discipline-specific proxy; the generic AutoCAD title does not establish automotive engineering.')
add('311903','7233.7','broader_proxy','Maintenance Technician services and repairs industrial machinery. Retain the industrial machinery mechanic profile; misleading Maintenance Technician aliases under welding occupations are rejected.')
add('311910','3115.1.16','close_match','Engineering Technician, Production matches Production Engineering Technician after word-order normalization; the 2020 duplicate-code decision does not change this ESCO occupational function.')
add('312215','1321.2.2','partial_proxy','Quality Control Supervisor leads industrial inspection, tests and corrective actions. Industrial Quality Manager covers the quality function better than general services quality management, but manager/supervisor seniority differs; reject the assembly-supervisor alias.')
add('313302','3122.4.2','close_match','Chemical Plant Supervisor coordinates operators, production quality and chemical processes. Chemical Processing Supervisor fits better than a control-room operator or a plant manager responsible for profit-centre investment budgets.')
add('314209','7126.6','close_match','Irrigator operates, adjusts and maintains irrigation systems in the inherited profile. Irrigation Technician is retained; the exact Irrigator alias under installation-only work is not enough to override the broader operational duties.')
add('315902','1324.3','broader_proxy','Logistics Supervisor coordinates storage and distribution. Logistics and Distribution Manager supplies the broader functional profile, with the supervisor/manager level difference retained.')
add('325105','3251.1','close_match','Dental Assistant is an alternate label for Dental Chairside Assistant and the supporting clinical duties align; do not infer dentist or practitioner status.')
add('325606','2269.8','broader_proxy','The 2020 radiographist-equipment role operates imaging equipment and positions patients. Radiographer fits the clinical imaging duties better than the inherited medical-equipment engineering technician; ECG/EEG and mixed modality coverage remain incomplete.')
add('363304','3433.1','close_match','Gallery Technician is an alternate label of Art Handler. Preparing, handling, moving and installing objects matches the inherited duties better than a conservator profession.')
add('363306','3433.1','broader_proxy','Museum Technician handles objects and supports exhibits. Art Handler covers those technical handling duties; collection-manager authority and all specimen/conservation work are not established.')
add('363414','3435.25.5','close_match','Stage Technician is an exact ESCO preferred occupation. The current cross-media profile is retained as context, not proof of every performance specialization.')
add('422602','4227.2','broader_proxy','Survey Interviewer collects government, social and market data. Survey Enumerator is retained as a broad survey profile; the Market Research Interviewer alias is narrower than the source scope.')
add('522313','5223.4','partial_proxy','E-commerce Sales Clerk handles product listings, orders and customer sales support. Sales Assistant is a test proxy; e-commerce platforms, fulfilment and channel-specific skills may be missing.')
add('818202','8182.1','close_match','Boilerman is an alternate label of Boiler Operator. Operation and maintenance, not manufacture of boilers, is the relevant function.')
add('818209','3131.3','partial_proxy','Engine Driver is stationary industrial internal-combustion plant work in the inherited profile. Retain the power-production operations proxy; reject the same-name Train Driver alias because the equipment and context differ.')

# Audit exact-label traps where an alternative label would change domain/level.
REJECT_EXACT={
 '213210':'Forestry Officer duties are professional forest management; Forest Ranger is only a possible conservation/protection component.',
 '213422':'Pathologist is a clinical specialist; Coroner adds a distinct death-investigation/statutory function.',
 '216601':'Public-service Designer grade does not establish Art Director authority.',
 '221211':'Neurologist is a clinical specialty; the Physicist alternate label is inconsistent with the ESCO occupation description.',
 '253120':'Information Security Officer does not automatically imply chief/executive ICT security authority.',
 '253130':'Cybersecurity analysis is not restricted to digital forensic evidence examination.',
 '254209':'Digital concept-art creation is different from conceptual fine art.',
 '254316':'Digital design spans media; the Web Designer alias is narrower.',
 '311132':'Generic laboratory work is not automatically bacteriology.',
 '311548':'Equipment Technician is not specifically a performance-equipment rental occupation.',
 '311831':'Assistant Surveyor is not specifically mine surveying.',
 '314405':'Aquaculture Technician is represented by an aquaculture profile; the broad agricultural technician alias does not require a change.',
 '321213':'Medical laboratory practice is not limited to bacteriology.',
 '321502':'Prosthetic fabrication technician scope differs from clinical prosthetist-orthotist assessment and fitting.',
 '363201':'Designer Grade B19 is not art-director seniority.',
 '431203':'Statistical Clerk includes statistics-specific support beyond generic data entry.',
 '821101':'Generic assembly is not automatically metal-products assembly.',
}

"""Project mapping decisions, not an official MASCO/ESCO equivalence crosswalk.

Syntax: MASCO roles | ESCO occupation code | relation | decision rationale.
c=close functional match; b=broader ESCO proxy; p=partial/narrower proxy.
The separate role-specific source excerpts remain in the mapping evidence table.
"""

DECISIONS = '''
111201|1112.6|b|Public-sector administration responsibilities; Malaysian rank is not represented.
112104|1330.3|c|Technical strategy and technology leadership align with chief technology officer.
121101|1211.1.1|p|Accounting management selected as primary; budgeting is an additional component.
121102|2412.3|p|Organisation-wide risk and governance; audit management is only partly represented.
121103|3312.3|c|Credit policy, lending control and credit-team management.
121104|1346.4|b|Insurance operations management; exact organisational scope may differ.
121105|2412.7|c|Investment fund and portfolio management.
121107 121111|2411.1.12|b|Tax advisory and compliance proxy; managerial level and transfer-pricing specialty need local enrichment.
121108|1346.5|c|Insurance claims management.
121109|2120.1|b|Actuarial valuation work; management responsibility is not fully represented.
121202|1213.7|c|Management of workplace health, safety and environmental programmes.
121404|1324.8|c|Supply-chain and logistics planning and coordination.
121408|1330.5|b|D11 description concerns IT infrastructure and services, not generic product technology.
121409|1120.3|p|Business leadership proxy; chief business officer is not identical to chief executive.
122301|1223.2|c|Research and development leadership, not a narrower product-manager alias.
131102|6130.1|b|Agricultural production and farm operations management.
131103|1120.1|p|Animal-facility operations and staff management; veterinary clinical oversight requires enrichment. D11 task text appears to describe turf maintenance and is excluded from this decision.
131104|6113.3|p|Turf maintenance and field-team supervision; horticulture proxy does not imply a tree-only occupation.
131201|1312.3|c|Aquaculture production management.
132102|3123.1.11|p|Electrical work supervision; ESCO supervisory seniority is below the managerial title.
132103|1349.12|c|Energy management responsibilities.
132104|1321.2.1|c|Industrial production management.
132105|1321.2.1|b|Shipyard hull production leadership; shipbuilding specialty is missing, not an onboard engineer.
132106|1321.2|p|Mechanical engineering and production management; technical mechanical-engineering content needs enrichment.
132107|7212.4|c|Coordination of welding quality, procedures and personnel.
132108 132109|1321.2.1.3|b|Food-production management; palm-oil/halal specialty is absent from ESCO.
132111|1219.5.3|c|Power-plant management.
132201|1322.1.1|c|Mine production management.
132202 132203|1322.1.2|b|Oil/gas production operations; offshore installation duties need enrichment, not renewable-energy management.
132205|1321.2.1.7|c|Metallurgical production management.
132302|1323.1|b|Building and architectural construction management.
132303|2165.4|b|Land surveying function; managerial seniority is not represented.
132401|1324.7|c|Railway station management.
132402|1324.3.1.5|c|D11 tasks concern fleet, driver and road-transport operations.
132404|4323.11|p|Port and shipping coordination; full managerial authority is not represented.
132405|1324.3|b|Logistics operations; Malaysian halal assurance requires separate enrichment.
151101|1330.2|p|CIO selected as the primary occupation of a composite CIO/CDO/CISO title; not all three skill sets are inherited.
151102 151103 151105 151111|1330.5|b|ICT service/infrastructure operations; local community-centre, network or managerial scope varies.
151104|1330.9|c|Internet service provision is telecommunications service/network management.
151106|2654.1.7|p|Technical AV direction and service coordination; venue/corporate AV scope differs from performance production.
151107|1330.7|c|ICT project management.
151108|1330.7|p|ICT project delivery proxy; multi-project programme governance is not fully represented.
151109|2131.3|b|Bioinformatics function; managerial responsibilities need enrichment.
151110|2431.7|b|Creative multimedia direction.
151112|2434.2|c|ICT business development.
151113|1330.5.1|c|ICT development management.
151118|1330.1|p|Data governance and team leadership; chief-level scope may exceed D11 manager seniority.
161201|1223.2|p|Plant bioactive/phytonutrient R&D leadership; food biotechnology and formulation are missing specialty skills.
161202|3253.1|b|Community health promotion and education; programme-level scope differs.
161203|2221.2|b|Professional nursing function; chief-nurse leadership is not encoded by the proxy.
211202 211203 211204|2112.1|b|Meteorology occupation; environmental/numerical-forecast specialty or public-service grade is not separately represented.
211403|2114.1|b|Geoscience proxy based on geological study; not every geoscience specialty is covered.
212101|2120.5|c|Mathematical professional work, not an assistant occupation.
212102 212105|2120.6|c|Statistical professional work; government grade is not an ESCO occupation.
212103|2120.1|c|Actuarial calculations, risk modelling and valuation.
212104|2112.2|c|Metrology measurement science, not meteorology.
213102|2131.6|b|Serological immunology research; serology specialty is not separately represented.
213104|2269.13.1|p|Cytological specimen analysis; scientist/technologist qualification scope needs review.
213106|2133.5|c|Ecological research.
213107|2133.9|b|Wildlife protection and conservation officer duties.
213201 213207|2132.2|p|Applied crop and agricultural advice; regulatory and public-officer duties are only partly represented.
213202|2132.2|p|Agronomy advice and agricultural demonstrations; extension-teaching specialty needs enrichment.
213203 213206|2132.5|p|Forest resource conservation and advice; enforcement duties differ from an advisory occupation.
213204|1312.3|b|Aquaculture operations coordination; managerial seniority may differ.
213208|2164.1|c|Land-use planning.
213301|2132.2|c|Agronomy.
213302|2132.1|c|Agricultural science.
213303|6113.2|p|Commercial flower and ornamental-plant production; scientific floriculture content is only partly represented.
213304|6112.1|p|Arboriculture component selected; broader horticultural work is not fully represented.
213305|2149.11.2|p|Wood technology and material analysis; engineering scope may differ.
213306|2250.9|p|Animal research proxy; veterinary emphasis may differ from livestock-production science.
213307|2133.7|c|Environmental scientific research.
213310|3257.1|p|Environmental inspection and pollution control; Malaysian statutory enforcement is not transferred.
213402 213405|2212.1|b|D11 describes clinical diagnosis; specialised doctor is a broader clinical proxy, not physiologist or coroner. Specialty skills require local enrichment.
213404|2131.7|c|Pharmacological research.
213406|2131.5|p|Biological fermentation processes; food-biotechnology scope may not cover every industrial application.
213407|6123.1|c|Bee breeding and cultivation.
213408|2131.4.8|p|Embryology/genetics research overlap; clinical embryology and assisted reproduction are not fully covered.
214102|2149.15|c|Robotics engineering preferred occupation, not a competing mechatronics alias.
214104|1222.1|p|D11 profile concerns corporate communication strategy, not telecommunications engineering; managerial level differs and taxonomy placement should be checked.
214105|2141.4|b|Non-computer system and process engineering; no computer-hardware specialization is inferred.
214106|2149.2.4|b|General systems design and engineering.
214107|2411.1.5|p|Engineering cost estimation and analysis; financial proxy lacks engineering specialty.
214108|2141.4.2|c|Production-process engineering.
214109|2149.11|b|Engineering of ceramic materials, not artistic ceramics.
214111|2141.4.2.1|b|SCADA and industrial automation engineering.
214115 215102 431108|3112.5|b|Energy-use analysis and auditing; electrical specialty, competency certification or assistant grade need local enrichment.
214201 214206|2142.1|b|Civil engineering scope; technologist/public-service grade is not separately represented.
214203|2142.1.4|p|Ground and foundation engineering overlap; geological engineering is not exact foundation design.
214208|3315.8|c|Building/property surveying, not mine surveying.
214402|7412.7|p|Lift installation and technical service; engineering design versus technician scope needs review.
214403 214405|2144.1|b|Mechanical engineering; engine or technologist specialization is absent.
214406|3119.2.1|c|Robotics engineering technology.
214605|4323.19|p|Vessel operations coordination and readiness; technical section leadership is only partly represented.
214606|2144.1.7|c|Hydraulic machinery, pumps and actuators align with fluid-power engineering.
214610|2146.3|b|Mining blasting and explosives engineering.
214913 311914|3257.5|p|Machinery/workplace inspection proxy; equipment-specific inspection and Malaysian authority need enrichment.
215103|3123.1.11|c|Electrical supervision.
215202|2152.1.7|b|Integrated-circuit package/assembly engineering, not only circuit design.
215302|2523.3|c|Computer-network systems engineering.
216302|2143.1|b|Green-technology design interpreted through environmental engineering; no ICT specialization is imposed.
216401|2164.4|c|Town and urban planning.
216602 216603|2166.9|b|Graphic/poster design; government grade is not art-director seniority.
217201|3152.3|p|Marine navigation proxy for hovercraft piloting; craft-specific qualification is absent.
217203 217204|3152.1|b|Deck navigation/operations; superintendent rank is not represented.
217206 315204|3115.1.9|p|Vessel safety inspection/survey is one component; registration, port administration and enforcement are not fully represented.
217303|2144.1.1|c|Aerospace/aircraft design engineering.
217306|3154.3|p|Aviation operational coordination; marine-service context is not represented.
217308 217309 217310 217311 217312 217313|3154.2|b|Pilot examination and aviation inspection; aircraft category and Malaysian licensing authority need enrichment.
217402|3154.3|b|Flight operations control, not data-centre control.
217501|1324.3.1.3|b|Rail operations management; executive grade may differ.
218101|1322.1|b|Mining operational management.
218202|1219.7|b|General quality assurance; not ICT-only quality assurance.
218203|1324.3.4|p|Stores and inventory management; manager seniority may exceed executive role.
218205|1349.21|p|Technical service coordination/customer support; management scope is broader than adviser.
218206|2149.11|b|Materials engineering and selection.
218207|1223.2.1|b|Product development; executive seniority may differ.
218301|1323.1|b|Construction operations and project coordination.
221101 221111|2211.1|c|General medical practice; public-service grade does not change occupation identity.
221102 221103 221104 221105 221106 221107 221108 221201 221202 221203 221204 221205 221206 221207 221208 221209 221210 221211 221212 221213 221214 221215 221216|2212.1|b|Specialised medical doctor umbrella; ESCO does not distinguish this clinical specialty. Do not substitute allied-health occupations or treat umbrella skills as specialty-complete.
221217|2269.4|c|Occupational therapy, not a physiotherapy alias.
222101 222104 322101 322102|2221.2|b|Nursing-care occupation; Malaysian registration/grade and practical-nurse scope must be checked locally.
222103|2310.1.28|b|Nursing instruction; teaching institution and clinical supervision scope may differ.
222201|2222.1|c|Midwifery.
224101|3258.2|c|Paramedic emergency clinical care.
225101|2250.6|c|General veterinary clinical practice, not statutory official-veterinarian status.
225102|2250.7|p|Public veterinary duties; local statutory scope and general clinical duties may differ.
226301|2263.3|c|Workplace health and safety advice.
226302|3257.5|b|Workplace chemical/exposure and hygiene assessment; not energy assessment. Malaysian competency requirements remain local.
226303|1321.2.5|b|Waste management; competency certification is not an ESCO equivalence.
226304|3112.1.2|b|Building inspection/audit; certification and audit scope need local review.
226305|2263.2|p|Food-safety and assurance proxy; halal religious, supply-chain and certification requirements are NOT represented by food-safety skills alone.
226307|2143.1.4|b|Waste-treatment engineering; landfill specialization requires enrichment.
226308|2149.10|b|Major-hazard engineering and risk control; Malaysian competent-person scope is not transferred.
226311|3257.5|p|Atmospheric hazard checks and confined-space safety; authorised gas-testing/entry-supervisor competence is not fully represented.
226312|3257.1|c|Environmental health inspection.
226402|2264.2|p|Rehabilitation/physiotherapy proxy; broader multidisciplinary rehabilitation is not fully represented.
226502|2265.1|c|Dietetics.
226503|1321.2.1.3|p|Food preparation and service management proxy; public-service/clinical dietary context may differ.
226603|2266.2|c|D11 explicitly describes speech, pronunciation and swallowing therapy; not orthoptics.
226903|2320.1.4|p|Health vocational instruction; paramedic and auxiliary-health scope extends beyond nursing/midwifery.
231104|2310.1.12|c|Dentistry lecturer.
231107|2310.1.31|c|Pharmacy lecturer.
238101 238102 238103 238104 238105 238106 238107|2320.1|b|Vocational teaching; subject specialty and Malaysian grade are not separate ESCO occupations.
239301|2356.1|b|Software instruction within ICT training.
242102|2120.5|p|Mathematical modelling and optimisation; operations-research application needs enrichment.
242401 351207|2424.2|b|Corporate staff training; call-centre specialization is not separately represented.
242601|2131.5|c|Food biotechnology.
242602|2131.4.1|c|Aquaculture biology.
242603|1223.2|b|R&D coordination; executive rank may differ.
242604 242606|1223.2.2|p|Research coordination proxy; scientist research duties and management seniority require review.
242607|1349.17|p|Laboratory operations, staff and budgets; medical laboratory context is narrower than general teaching/research laboratories.
243103|2433.4|c|Technical sales engineering; corrects the D11 promotion-assistant crosswalk.
243104|2433.6|b|Technical product demonstrations, customer advice and sales support.
243302|3114.1.5|p|Haematology-device installation, calibration and user support; applications training and clinical specialty need enrichment.
243402|2514.2|b|D11 describes mobile/internet-banking application development, not bank branch management.
251102 251401 251403|2512.4|b|Software development; .NET/C/C++ language specialization is not separately inherited.
251103|2152.1.7.1|c|RTL hardware description and digital integrated-circuit design, not application software.
251104|2511.14|p|IT-system architecture and design; software/network implementation details vary.
251203 251404 252201 351106|2522.1|b|Information-system and infrastructure administration; grade/specialty varies.
251301 251302|2513.5|c|Web development.
251405|2512.5|p|User-interface programming component selected; gameplay development is not fully represented.
251903|2511.11|b|AI/machine-learning engineering overlap.
252105|2521.1|b|Database administration; Oracle specialization requires local enrichment.
252202 252203 252204 351103 351108 351203|3512.4|b|ICT user support and system troubleshooting; engineer/officer/assistant rank is not inferred.
252211|2511.13|b|ICT feasibility, analysis, design and implementation; not chief-information-officer authority.
252403|2521.2|c|Data architecture/database design is an ESCO alternate label; corrects the older ICT-system-analyst assignment.
253101 253104|2529.8|p|Cybersecurity risk, governance and vulnerability analysis; incident-response duties and seniority may differ.
253103 253106|2529.6|b|Security infrastructure, controls and administration; no chief-level authority is inferred.
253107|2513.4|p|Online-content review/moderation component; content management is only a proxy and does not establish safety-evaluator equivalence.
254101|2166.13|b|Digital compositing and visual-effects work.
254104 254105 254304|2166.7|b|Digital visual/media design; visualization and multidisciplinary design specialties need enrichment.
254106|3512.4|b|D11 profile is system maintenance and ICT user support, not theoretical computer science.
254107|2641.4|c|Story/content writing.
254108|2166.1|p|3D modelling component; generalist animation, lighting and effects scope is wider.
254203|1223.2.1.3|c|Games production and development management.
254204|2166.5|b|Digital concept-art production; game/film pre-production specialization is not separately represented. Avoid fine-art conceptual-artist alias.
254205|2166.5|p|Digital-art production proxy; technical pipeline, shaders and programming need enrichment.
254206 254305|2431.7|b|Creative direction; composite performing-media roles need further specialization.
254207|2513.1|p|Games graphics programming; a software occupation is used, not graphic design.
254303|2513.3|p|Interface design component of UX; user research and broader service experience are not fully covered.
254306|2166.3.1|p|Character deformation/rigging in 3D animation; not physical rigging or desktop publishing.
291606|5419.3|p|Coastguard maritime safety, monitoring and search/rescue; Malaysian superintendent command and enforcement authority need enrichment.
311108|3111.4|c|Geological technical work.
311109|3111.5|p|Marine/hydrographic measurement; biological and chemical oceanography are not fully covered.
311112 311116|3141.2|b|General scientific laboratory work, not an arbitrary bacteriology specialty.
311202|2149.14|p|Construction quantities/cost estimates; chartered/professional scope may exceed technician.
311203 311806|3118.3.4|b|Civil design drafting; engineering design responsibility may differ.
311204|3123.1|c|Construction-site supervision.
311207|3117.2|c|Geotechnical support.
311211|3114.1.4|c|Process instrumentation; not musical-instrument work.
311214|5153.1|p|Building maintenance/caretaking proxy; green-building systems and technical energy expertise need enrichment.
311216|3115.1.6|p|Industrial maintenance coordination; assistant-engineer versus supervisor scope differs.
311217 311220|2149.14|b|Quantity-surveying function; assistant grade is not separately represented.
311222|3315.8|b|Building/property surveying function; assistant grade is not separate.
311304 311402 311503 311604|2421.1.1|b|Manufacturing/engineering cost estimation; electrical/electronic/mechanical/chemical specialty varies.
311308|3113.1|c|Electrical engineering technical support.
311404|3114.1.6|b|Semiconductor/microelectronics technical work.
311507|7223.4|p|CNC operation/programming component; technician maintenance duties are wider.
311510|3257.5|p|Workplace exposure and hygiene inspection; D11 mixes routine cleaning with competent-person hygiene assessment, so validate the duty scope.
311511|3115.1.11|c|Mechatronics technical support.
311512 311518|3118.3.5|b|Computer-aided design/drafting; CAM manufacturing or specific software skills need enrichment.
311515 311520|7233.7|b|Industrial equipment repair and maintenance; equipment type is not separately represented.
311602|3134.3|p|Petroleum-processing monitoring, sampling and operation; technologist/technical-supervision scope differs from control-room operation.
311704|3112.8|b|Field engineering technical assistance; industry is not specified reliably by D11.
311810|3112.10|c|Surveying technical assistance.
311906 311907|3141.1|b|Biotechnology laboratory/research support; agricultural/aquatic specialization needs enrichment.
311909|3119.16|b|General product testing and quality-engineering support; not an arbitrary hardware-only specialization.
312202 312204|3122.4|b|Manufacturing process supervision; finishing/cutting material specialty is unspecified.
312203|3122.4.2|c|Chemical compounding supervision.
312205 312206|3122.4.16|b|Wood production and inspection supervision.
312207|3122.4|p|Production supervision; food processing and halal controls require separate skills.
312208|2263.2|p|Food safety/quality proxy for halal meat assurance; religious certification and supervisory scope are not covered.
312213|7511.6.1|p|Halal slaughter technical practice; supervisory responsibilities are not fully represented.
312214|1324.3.4|p|Warehousing leadership; halal segregation and assurance need local enrichment.
312301|3123.1|b|D11 construction-group operational supervision.
313102|7213.1|p|Metal fabrication/assembly component; power-plant operation is additional, not textile weaving.
313201 818202|3131.3|p|Stationary engine/power generation operation proxy; engine type and Malaysian competency certification require review.
313501|3135.1|b|Metal-process furnace control; exact process may vary.
314102|3141.2.5|b|Zoological laboratory support with entomology specialization.
314205|2132.6|p|Livestock husbandry guidance; supervision and halal assurance are not fully represented.
314206|3142.1|c|Agricultural technical assistance.
314208|6111.1|p|Estate/crop field supervision; oil-palm/rubber and scheme-administration duties need enrichment.
314303|3143.1|b|Forestry conservation technical support.
314304 314305|2133.9|p|Wildlife conservation operations; assistant grade and enforcement mandate differ.
314403 314405|6221.11|b|Aquaculture stock/water/environment technical support, not ship engine mechanics.
314404|6221.5|c|Hatchery operational assistance.
314407|2132.4|p|Fisheries advice and management support; assistant grade and statutory duties differ.
315103|7232.5|b|Aircraft restoration and maintenance; restoration specialty needs enrichment.
315108|3154.1|b|Air-traffic control support; assistant authorization differs.
315201|4323.11|p|Port berthing coordination; navigational authority and vessel piloting are not fully represented.
315203|3343.1|p|D11 duties are ship-registration records, revenue and administration, not marine-engine repair.
315302|3112.1.10|b|Rail infrastructure maintenance, not computer-network work.
315303|7421.6|b|Rail signalling/electronic systems maintenance.
315901|1324.3|b|Logistics coordination and supervision.
315902|2133.15|p|Environmental/green infrastructure technical support; facilitator role is not an exact technical occupation.
321201|2133.15|b|Ecological/environmental technical monitoring.
321202|2269.12|b|Histological/anatomical pathology laboratory practice.
321203|2269.13.1|c|Cytological laboratory analysis.
321206|2269.13|p|Biomedical specimen analysis; local technician qualification and supervised scope differ from scientist designation.
321207|3259.1|p|Operating-room technical support; anaesthesia is a narrower proxy than all surgical technology.
321501|2269.15|c|Prosthetic and orthotic fabrication technology.
321502|3114.1.5|p|Treatment-accessory fabrication and medical equipment QC; radiotherapy mould-room specialty is absent.
324107|3240.2|b|Veterinary technical assistance; government grade differs.
325303|3253.1|p|Community health support; licensed nursing scope is not fully represented.
325502|3255.2|c|Physiotherapy technical assistance.
325503|2634.2.4|b|D11 describes stress counselling and psychotherapy, not massage.
325603|3114.1.5|p|Diagnostic equipment technical work; clinical imaging authorization is not inferred.
325604|2269.8.1|b|Diagnostic imaging umbrella; ultrasound specialty requires enrichment.
325605|2310.1.28|p|Clinical health instruction; nursing teaching is narrower than all allied-health clinical instruction.
325607|3258.2|p|Clinical paramedic-level assessment/treatment proxy; Malaysian assistant medical officer scope is distinct.
325704|2133.13|p|Water quality sampling/analysis; inspection authority needs local enrichment.
325707|3119.5|c|Food technology technical assistance.
325709|2133.15|p|Environmental monitoring support; statutory inspection/prosecution duties are not fully represented.
325801|3258.2|b|Ambulance clinical/emergency care; local officer role may differ.
351102 351104|3511.1|b|Computer/data-processing operations, not CNC machine operation.
351105 352109|3522.1|b|Telecommunications technical support; grade/seniority varies.
351201|3512.1|c|ICT help-desk/user support.
351204|3513.2|b|ICT network/communications technical support, not corporate communication management.
351205|2521.1|p|Database administration support; assistant authority differs from full DBA.
351206|2514.2|p|Application programming support; assistant grade and independence differ.
351208|3511.1|b|Data-centre operations; supervisory responsibility needs enrichment.
351402|2166.9|p|Creative production/design support; assistant scope is not a full designer equivalence.
352104|3152.1|p|Shipboard communications/navigation component; dedicated radio-officer specialty is not represented.
363206|7317.6|p|Wood carving proxy; stone/synthetic carving is outside this occupation.
363209|2166.9|b|Graphic design; grade does not imply art-direction authority.
363301|2621.3|p|Collection handling/preservation support; conservator qualification and full restoration scope exceed technician.
411106|3343.1|p|Public programme administration support; inspections and economic-development advisory duties require enrichment.
431101|3339.2|p|Auction administration overlap; clerk is not authorized auctioneer.
431103|4214.1|p|Credit/debt follow-up component; broader account control differs from debt collection.
431106 431204 431209 431218|3313.1|b|Accounts, transaction corrections and finance support; specialty/grade is not separately represented.
431107|5230.1|c|Cash handling/cashier function.
431109|4312.1|p|Audit/compliance documentation support; general regulatory compliance is wider than financial auditing.
431110|4312.1|c|Audit support and records; corrects the prior sales-support-assistant mapping.
431201|3314.2|c|Statistical support work, not generic data entry.
431210 431212|4312.2.1|b|Securities/brokerage back-office administration.
431211|4311.1|p|Rate calculation and billing component; insurance/transport tariff specialization is not fully represented.
431213|3312.5|p|Loan documentation and collateral administration overlap; full loan-officer assessment authority is not implied.
431214|3312.6|p|Mortgage application/document review; underwriting decision authority exceeds clerical support.
431216|5223.4|p|Sales support proxy; e-commerce platform/order processing needs enrichment.
431217|4312.6|b|Property/leasing administration; non-property leasing may differ.
531204 531205|2320.1|p|D11 explicitly describes vocational curriculum development and teaching; assistant grade differs from a full teacher, but early-years teaching is inappropriate.
532106|3253.1|b|Public/community health support.
821101|8211.2|p|Industrial mechanical assembly selected from broad assembler scope; electronic/aerospace subtypes differ.
213309|2133.6|b|Environmental impact, sustainability and regulatory advice/programmes; exact consulting specialization varies.
214302|2133.7|b|Environmental data, research and compliance analysis; source does not primarily describe engineering design.
214601|2146.8|p|Mine planning/extraction engineering component; broad mining lifecycle exceeds mine-planning specialization.
217202|4323.11|p|Port-side vessel and cargo coordination, not command of a ship at sea; port-captain seniority differs.
311110|3117.2|b|Slope/terrain monitoring and geotechnical risk support.
311521|7311.2|p|Optical component assembly/calibration; engineering R&D and testing are wider than the assembler proxy, but eyewear dispensing is inappropriate.
321204|2269.13|p|Clinical specimen analysis described by D11; physiology specialization and technician qualifications require local review.
324101 324103|3141.1|b|Biotechnology research/production technical support; veterinary products and animal context need enrichment.
325104|2261.3|p|Preventive oral-health care proxy; Malaysian dental therapists diagnose/treat children beyond a hygienist scope. Do not infer licence equivalence.
315301|3115.1.18|b|Rolling-stock technical installation, maintenance and testing; local supervisory scope varies.
'''

def overrides():
    out = {}
    for line in DECISIONS.strip().splitlines():
        ids, esco, relation, rationale = line.split('|', 3)
        for code in ids.split():
            if code in out:
                raise ValueError(f'Duplicate curated decision: {code}')
            out[code] = {'code': esco, 'relation': relation, 'rationale': rationale}
    return out

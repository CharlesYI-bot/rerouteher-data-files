"""Project-reviewed MASCO 2020 identity decisions, not an official crosswalk.

Exact normalized titles are handled separately. No fuzzy score authorizes a match.
Multiple targets are explicit components of a current merged occupation/grade.
Excluded records are retained in the audit, not declared nonexistent professions.
"""
DECISIONS={}

def add(source,targets,method,reason,confidence='medium'):
    assert source not in DECISIONS,source
    DECISIONS[source]={'targets':targets.split() if isinstance(targets,str) else targets,
                      'method':method,'reason':reason,'confidence':confidence}

# Same named public-service occupation, reverted to an entry actually printed in
# MASCO 2020. JPA SSPA Annex B documents the grade transitions (not MASCO codes).
GRADE_PAIRS='''
211204 211201
212105 212101
213107 213101
213206 213202
213207 213203
213208 213204
213310 213301
214206 214202
214207 214245
214208 214246
214913 214922
216102 216101
216202 216201
216404 216401
216503 216501
216504 216502
216603 216601
217206 217201
217308 217301
217309 217302
217310 217312
217311 217313
217312 217314
217313 217315
217404 217401
222104 222101
225102 225101
226102 226101
226202 226201
226203 226207
226312 226301
226402 226401
226502 226501
226503 226514
226702 226701
226903 226902
231104 231105
231107 231117
238102 238101
238103 238109
238104 238110
238105 238111
238106 238112
242606 242601
242607 242602
252211 252201
291602 291603
291606 291608
311113 311101
311114 311102
311115 311133
311116 311136
311117 311137
311219 311219
311220 311232
311222 311237
311804 311801
311805 311826
311806 311827
311807 311828
311808 311829
311809 311830
311810 311831
311914 311929
314206 314216
314207 314217
314208 314221
314303 314304
314304 314305
314305 314306
314407 314407
315107 315115
315108 315116
315203 315201
315204 315208
321102 321101
321303 321305
321502 321503
322102 322101
324107 324110
325103 325101
325104 325107
325303 325305
325607 325615
325707 325747
325708 325748
325709 325749
331401 331401
351107 351101
351108 351125
352111 352101
363209 363201
411106 411126
431110 431126
431218 431201
431219 431231
531204 531208
531205 531210
532106 532102
'''
for line in GRADE_PAIRS.strip().splitlines():
    source,target=line.split()
    add(source,target,'grade_reversion',
        'Same named occupational service; use the MASCO 2020 title and its printed SSM grade. JPA SSPA Annex B supports the grade-family transition. Only grades listed in the 2020 index are retained.','high')

TITLE_PAIRS='''
121108 121115
132205 132210
132405 132416
211203 211211
213104 213117
213402 213409
213403 213410
213404 213416
215202 215236
215302 215323
216403 216407
218101 218101
221108 221118
226303 226328
226308 226344
226501 226502
226601 226601
232101 232102
243302 221266
251202 251219
251203 251243
251405 251434
252201 252205
253107 253139
254302 254302
311512 311538
312207 312218
312208 312220
312213 312228
312214 312229
313105 313113
314205 314218
351106 351124
'''
for line in TITLE_PAIRS.strip().splitlines():
    source,target=line.split()
    add(source,target,'title_variant',
        'Same occupational identity after word-order, singular/plural, spelling, acronym-position or explicit competent-person title-wrapper variation. Preserve the official 2020 printed title.','high')

EQUIVALENTS=[
('121101','121104','Budget planning, forecasting and expenditure control are the stated core duties; Budget Manager is the 2020 counterpart. Financial-accounting wording remains in the source-title audit.'),
('121105','121109','Fund and portfolio management denote the same investment-fund management occupation.'),
('132104','132102','Manufacturing production management corresponds to the 2020 production-and-operation manager, manufacturing.'),
('132404','132414','Current duties are shipping schedules, cargo movement and port/shipping logistics management; retain the 2020 Shipping Manager identity.'),
('151103','151108','The added information-technology qualifier clarifies the same Village Community Center Manager occupation.'),
('151118','151113','Current description explicitly oversees data systems and data operations; use the 2020 Data Operations Manager counterpart, with broader governance scope retained as a source caveat.'),
('161203','161202','Head-of-nursing leadership, nursing policy, staffing and hospital nursing operations correspond to Director, Nursing.'),
('212102','212106','The current generic statistician performs applied statistical analysis; retain the 2020 applied-statistics occupation, not a public-service grade or every statistical specialty.'),
('214403','214413','Same internal-combustion-engine engineering occupation; current competent-person qualification is provenance, not an invented 2020 qualification.'),
('214610','214649','Blasting Expert within the mining group; the added Mine qualifier is not a distinct occupational identity.'),
('218204','818202','Same boiler operation and maintenance occupation. Current competent-person/supervisory details are retained as source context, not as 2020 certification evidence.'),
('226311','226324','Authorised Gas Tester is the named 2020 occupation; confined-space entry supervision is described in the current combined scope and retained as a limitation.'),
('226902','226901','Radiographer and X-Ray Technician refer to the same radiography service; current U9 is reverted to the printed U41 title. Do not interpret as a qualification or licensing crosswalk.'),
('243104','243114','Product Specialist in the sales/marketing group corresponds to Trade Product Specialist; no engineering-product role is substituted.'),
('252105','252108','Oracle database administration is the database-management function of the 2020 Oracle Database Specialist; preserve this functional-title judgement as medium confidence.'),
('254108','254206','The described multi-stage 3D asset creation role is a 3D Artist; retain any more exact source row as primary if both map to this same 2020 code.'),
('254206','254211','Current description and tasks specifically lead visual/artistic direction and a creative design team; Art director is the supported 2020 role, not every performing-arts director.'),
('311111','311125','Climate Science Technician and Climate Service Technician share climate-data collection, equipment support and reporting duties.'),
('311511','311524','Mechatronics engineering support, controls integration, assembly and testing correspond to Mechatronics Technician; do not substitute a purely mechanical technician.'),
('311518','311544','Current AutoCAD Designer prepares technical CAD drawings; AutoCad Drafter is the 2020 occupational counterpart.'),
('311520','311903','The current role performs machinery/equipment servicing, diagnosis, repair and preventive maintenance: Maintenance Technician.'),
('312218','312215','Current manufacturing QA supervision explicitly includes inspection, testing and quality-control personnel. Use the 2020 Quality Control Supervisor and preserve the QA/QC wording judgement.'),
('313301','313302','Chemical processing plant controller/supervisor has the same plant-supervision function as Chemical Plant Supervisor.'),
('314203','314209','Current role operates, adjusts and maintains agricultural irrigation systems; the corresponding 2020 agricultural technician title is Irrigator.'),
('315901','315902','Retain the logistics-supervision occupation explicitly named in the current combined title; do not infer road-only or halal specialisations.'),
('325101','325105','Dental aide/assistant is the same supporting occupation as Dental Assistant; keep the distinct graded dental-surgery assistant separate.'),
('325503','282407','Current description explicitly identifies psychotherapy/mental-health treatment and says the role may be known as a psychotherapist; do not map it to massage or acupressure.'),
('325603','325606','Current core function is operation of general medical radiographic/diagnostic equipment; use the 2020 general-medical radiographist-equipment occupation, retaining the current wider modality scope as a caveat.'),
('363401','363414','Stage Technician is explicitly within the current stage/broadcast production role; broad cross-media tasks are inherited source context, not 2020-specific task evidence.'),
('422601','422602','Survey enumeration/interviewing corresponds to Survey Interviewer.'),
('431216','522313','Current description is online retail assistance: listings, orders, customer enquiries and sales support. E-commerce Sales Clerk is the 2020 retail counterpart, not a software role.'),
('818202','818209','Same stationary-engine operation within the boiler/engine-plant operator group; retain current internal-combustion/competent-person qualifiers in provenance.')]
for source,target,reason in EQUIVALENTS:add(source,target,'reviewed_functional_equivalent',reason)

SPLITS=[
('121404','121411 132405','Current title explicitly combines supply-chain and logistics management; retain the two printed 2020 identities.'),
('131201','131202 131203','Current combined role names both fishery production/operation and aquaculture production management.'),
('151101','151101 151102 151103','Current title explicitly merges Chief Information Officer, Chief Data Officer and Chief Information Security Officer.'),
('151105','151117 151123','Current title/duties combine network management and ICT infrastructure management; do not include unrelated public-relations communications roles.'),
('151113','151112 151135','Current role explicitly manages both application and software development; both are distinct printed 2020 occupations.'),
('212103','212112 212113','The generic current actuary explicitly performs pricing and valuation/reserving. Retain these 2020 specialisations; do not infer the formal Appointed Actuary status.'),
('213304','213306 213169','Current title explicitly names Horticulturist and Arborist, which have separate 2020 codes.'),
('221111','221101 221120','Combined UD9/UD10 source maps to printed UD41/UD43 entries; JPA Annex B documents UD9=UD41 and UD10=UD43/44.'),
('226302','226325 226327','Current assessor description explicitly covers indoor-air-quality and chemical exposure assessment; both appear as named 2020 occupations.'),
('238107','238103 238106 238107 238108','The combined DV5/DV6/DV7/DV8 source maps to printed DV29/DV35/DV37/DV39 entries; JPA Annex B lists these grade-family transitions.'),
('251903','252411 252413','Current title explicitly combines Machine Learning Engineer and Artificial Intelligence Engineer, each printed separately in 2020.'),
('254104','254120 254305','The current composite title explicitly includes Multimedia Artist and Multimedia Designer; retain those 2020 identities, without inventing a generic 2020 animator code.'),
('311504','311516 311517','The current dockmaster manages docking and dry-docking. MASCO 2020 distinguishes dry-dock and graving-dock dockmasters.'),
('311510','311531 311552','The current generic competent-person hygiene technician has two named 2020 hygiene-technician entries. Existing D11 task-scope warning remains; these are test-only inherited profiles.'),
('363301','363304 363306','Current combined title explicitly names both Gallery Technician and Museum Technician.')]
for source,targets,reason in SPLITS:add(source,targets,'combined_title_split',reason)

add('311901','311910','duplicate_2020_title_canonical_choice',
    'The 2020 index prints equivalent Production Engineering Technician titles at 3119-10 and 3119-15. Use the lower code as the project canonical entry; retain 311915 as an alternative, not a second duplicate role.')

EXCLUSIONS={
'111201':('aggregate_no_unique_2020_identity','Current row is the broad Senior Government Officials category, while 2020 six-digit entries identify specific offices. Do not substitute the Keeper of the Rulers Seal or arbitrarily expand all offices.'),
'121111':('no_verified_2020_equivalent','Transfer Pricing Consultant exists in 2020, but no equivalent managerial occupation was verified; a consultant is not silently substituted for a manager.'),
'121409':('no_verified_2020_equivalent','No Chief Business Officer entry or unambiguous same-level identity was verified; CEO and compliance officer are different roles.'),
'214108':('aggregate_no_unique_2020_identity','Current row combines many manufacturing/material technologist specialties. The 2020 petroleum Production Technologist is not an equivalent manufacturing-wide occupation.'),
'214408':('no_verified_2020_equivalent','No mine-ventilation-engineering entry verified; a general HVAC engineer would not establish this mining specialty.'),
'214911':('no_verified_2020_equivalent','No Nano Engineer/nanotechnology-engineering occupation verified in the 2020 index.'),
'218207':('no_verified_2020_equivalent','Product Development Executive is not the same as the printed Production Executive or Product Development Engineer.'),
'226310':('no_verified_2020_equivalent','No Ergonomist identity verified; related health/safety occupations are not sufficient to establish the same six-digit role.'),
'311110':('no_verified_2020_equivalent','No Slope Monitoring Technician identity verified; general geological or soil technicians are only broader candidates.'),
'311519':('no_verified_2020_equivalent','No Pneumatic Supervisor identity verified; general mechanical supervisors are not the same identified role.'),
'311521':('no_verified_2020_equivalent','2020 has Optical Engineer and optical craft occupations, but no verified Optical Engineering Technician counterpart at the same occupational identity.'),
'311811':('grade_entry_not_in_2020','JPA maps JA7 to JA38, whereas the 2020 index only supplies this named planning-officer entry at JA29. Do not mislabel a JA7 source as the JA29 grade entry.'),
'311907':('no_verified_2020_equivalent','2020 Aquaculture Biotech Production Technician differs from this Research Technician. Research and production are not treated as equivalent merely to retain a row.'),
'314204':('aggregate_no_unique_2020_identity','Current animal-production farming technician spans livestock specialties; dairy and poultry entries are narrower candidates, not a verified general identity.'),
'323101':('aggregate_no_unique_2020_identity','Current row combines several traditional/complementary medicine systems. The 2020 index lists distinct practitioners; no single unique occupation is established by the aggregate row.'),
'324105':('no_verified_2020_equivalent','No Animal Therapist identity verified; veterinary assistant or nurse is not an equivalent rehabilitation/behavioural-therapy occupation.'),
'351402':('no_verified_2020_equivalent','No Creative Assistant identity verified; full artist/designer roles are not silently substituted for the assisting role.'),
'431109':('no_verified_2020_equivalent','2020 compliance officer/analyst/executive entries do not establish the same assistant-level occupation.'),
'431217':('no_verified_2020_equivalent','2020 Leasing Executive is not established as the same assistant-level occupation.')}
for source,(method,reason) in EXCLUSIONS.items():add(source,[],method,reason,'not_established')

-- DATA ONLY. Existing permanent schema/constraints/indexes are not changed.
-- Target: rerouteher_test / postgresql-database-wxnjpd2ia8avtwbs739mtamk.
-- Requires fresh backup and action-time deletion approval before execution.
-- HOLD LIVE COMMIT: core-only data exposes the deployed empty-band scoring bug.
-- Also requires tested backend compatibility: -v backend_compatibility_confirmed=true
-- Default: transaction rehearsal with ROLLBACK. Commit: -v fix_commit=true
-- Supply -v backup_path=/validated/path/before.dump -v backup_sha256=...
\set ON_ERROR_STOP on
\if :{?fix_commit}
\else
\set fix_commit false
\endif
\if :{?backend_compatibility_confirmed}
\else
\set backend_compatibility_confirmed false
\endif
\if :fix_commit
\if :backend_compatibility_confirmed
\else
\echo STOP: fix and test role resolution, skill IDs, and empty-band scoring before activating this data
\quit 3
\endif
\endif
\if :{?backup_path}
\else
\echo STOP: backup_path is required
\quit 3
\endif
\if :{?backup_sha256}
\else
\echo STOP: backup_sha256 is required
\quit 3
\endif
BEGIN;
SET LOCAL lock_timeout='15s';
SET LOCAL statement_timeout='5min';
SET LOCAL application_name='rerouteher_data_quality_fix_20260830';
SET LOCAL search_path=rerouteher,public;
SELECT set_config('quality_fix.backup_path', :'backup_path', true),
       set_config('quality_fix.backup_sha256', :'backup_sha256', true);

-- Temporary work tables disappear at transaction end; original 35-table schema stays intact.
CREATE TEMP TABLE fix_role_map(old_id text PRIMARY KEY, new_id text UNIQUE) ON COMMIT DROP;
INSERT INTO fix_role_map VALUES ('R01','M251201'),('R02','M252403'),('R06','M254302');
CREATE TEMP TABLE fix_skill_patch(skill_id text PRIMARY KEY, old_name text, old_definition text,
 canonical_name text, skill_type text, embedding_text text) ON COMMIT DROP;
INSERT INTO fix_skill_patch VALUES
('ONET_2_A_1_e','Mathematics','Using mathematics to solve problems.','Mathematics (O*NET Skill)','technical','[-0.01379558,0.02006776,0.03928999,0.03176249,-0.11615294,-0.04617393,0.07589681,0.04743307,0.00249894,0.02056443,-0.03905313,0.02347851,0.00641430,0.08650790,-0.03166593,0.05811797,-0.07057307,0.05606921,-0.03785439,-0.09188766,-0.01788604,-0.00750453,-0.00709359,-0.05858016,0.07544124,0.00353484,-0.00791772,-0.04494255,0.05997726,-0.03048637,-0.03274830,0.07546497,-0.00706995,0.00445758,-0.07421577,-0.00406645,-0.00891639,0.08278213,-0.04261206,0.04398466,-0.01510151,-0.04360611,0.06352680,-0.01547841,0.03589827,0.02626251,-0.00817516,-0.00153714,-0.00417943,-0.00790364,-0.07830703,-0.02757232,-0.09774245,-0.03866064,0.11998086,-0.00733360,0.02770858,0.01546747,-0.04683692,-0.03517460,0.02483697,0.00411480,0.00190226,0.03295399,0.06132873,0.03047864,-0.03998054,-0.00898641,-0.08556062,0.06498232,0.02321700,0.03871146,-0.04631015,0.09310437,0.13920853,-0.05094168,0.05969052,-0.00300834,0.04391517,0.04095098,0.04638110,-0.03381709,-0.05399457,0.02492671,-0.01434223,-0.04763779,-0.02958300,0.05235416,0.05262318,-0.13169949,0.04709876,-0.06311575,-0.03045091,0.02108326,0.02501680,-0.03367991,-0.01320874,0.02228014,-0.08070813,0.05971198,0.00972482,-0.00701236,-0.03798945,0.00150017,-0.04575882,0.04731483,0.07606141,0.02940865,0.04805192,-0.07640590,-0.04916383,-0.02561742,-0.02828408,0.05366979,0.01270466,-0.01699078,0.00493332,0.01949781,0.06013175,0.05405057,-0.02968840,0.08640289,-0.00746778,0.02786984,0.03788383,0.04302341,-0.03215819,-0.00000000,-0.06191502,0.03018483,0.05960176,0.02218010,0.04866496,-0.04459856,0.02755106,0.00327879,0.10851263,0.05991943,-0.00490856,0.03940830,0.00343725,0.06086577,0.15259402,-0.00471945,0.00359487,-0.00671404,-0.00606705,0.03382433,-0.02335902,-0.08264434,-0.00475295,0.00325848,-0.02805085,0.03638780,0.02483174,-0.03182219,0.09771530,-0.00706226,0.01258555,0.06594041,-0.11626901,0.00886669,0.00099098,-0.01115667,0.03492983,-0.05073070,0.11496409,-0.00181891,-0.06659741,-0.00410190,0.03257713,0.04794657,-0.02818973,0.03948691,0.06090236,0.04285641,0.00288222,0.04015396,-0.08982890,0.02037684,-0.02413049,-0.10678805,0.06384075,0.02095523,-0.03830407,0.03143380,0.00812010,0.06576396,0.04734634,0.02716468,-0.03002139,-0.03674919,-0.11928806,0.04681004,-0.07358080,0.00248959,0.14646992,-0.01990891,-0.07267369,0.01240597,-0.03113420,-0.00419119,0.00047271,-0.02791339,0.02492343,-0.02304273,0.03440633,0.05579108,0.07840227,0.02916433,0.04088522,-0.10488284,-0.01247580,-0.01768703,0.04643952,-0.08250394,0.04954991,0.00572310,-0.00941512,-0.04443125,-0.02806026,0.02420877,-0.04098722,0.00000000,-0.12695915,0.04264309,-0.12479785,0.05718238,-0.02397947,-0.01056199,0.01324258,-0.11116852,0.04118460,-0.00271385,-0.01674859,0.03765584,-0.04950809,0.03504196,-0.03941729,-0.10728630,-0.11252788,0.00238981,-0.04563513,0.00306154,-0.06059625,0.04893227,-0.05158779,-0.02782519,0.02225389,-0.00605328,-0.02873449,-0.04164078,-0.08084919,0.08969176,0.00628174,-0.07761690,0.01814917,-0.05916668,-0.03011966,0.01511762,0.07779623,-0.01571335,-0.02652621,-0.01716985,0.00022728,-0.09539039,0.03039951,0.00051517,-0.00957753,0.00649424,-0.00564157,-0.00451513,0.00021725,0.07695299,0.04733089,-0.02649589,0.04226608,-0.08032522,-0.00387325,0.06118865,-0.00920811,-0.08986486,-0.00944594,0.02430249,-0.02479642,-0.02641509,0.03271114,0.09246585,-0.01862896,-0.00662351,-0.03809555,0.06852971,-0.03888634,-0.01123785,-0.06217048,0.05806207,0.01874827,-0.01844077,-0.04542488,-0.01692285,-0.06811318,0.07257615,-0.03995218,-0.01118502,-0.07040440,-0.06588341,0.00522247,-0.00528520,-0.10404089,-0.00526789,0.13193484,-0.01332097,0.00907560,-0.10464858,-0.08211074,0.01209591,-0.06850393,0.00047739,-0.01058625,-0.00000002,-0.05672405,0.01870073,0.03989193,-0.05814061,0.02770093,0.03998226,-0.01490378,0.01031649,-0.07434629,0.06740934,0.00518489,0.03930664,-0.01514796,0.01442481,0.05388707,0.01666606,0.08520213,0.03336166,-0.02233127,-0.04392070,0.12293517,0.01964608,0.00556132,0.06123409,0.01349363,0.02338795,0.01720252,0.06825630,0.00953479,0.02449300,-0.01981718,-0.03770270,0.00460447,-0.02827221,-0.00615083,-0.00466014,0.04148284,-0.00297564,-0.02055555,0.00457658,-0.09325022,0.05536056,0.04019649,0.00164235,0.09098301,-0.00500443,0.04281195,0.00906419,-0.00646053,-0.05223545,0.02217298,0.07090580,-0.06837432,0.03974598,0.04819348,-0.09136478,-0.02457321,-0.03554612,-0.15756406,0.10929225,0.01512065,0.05380711,-0.01072173,0.01408472]'),
('ONET_2_B_3_e','Programming','Writing computer programs for various purposes.','Programming (O*NET Skill)','digital','[-0.03853039,0.00687063,-0.00152493,0.05443277,-0.05624406,-0.07550192,0.10698188,0.08070190,-0.03700189,0.00328219,-0.04915535,0.02890580,0.01805750,-0.02459723,-0.02636420,0.03885870,-0.05425535,-0.02071803,0.02680607,-0.10173921,0.01170655,-0.00928073,-0.01210963,-0.06106680,0.07223830,0.05839956,-0.00188042,-0.05775931,0.05626798,-0.01488616,-0.06102689,0.07764174,0.06139998,0.05453682,0.05331039,0.02311930,0.03074779,0.00667468,-0.06009203,-0.04608081,-0.07535861,0.01690634,0.02367242,-0.01387295,0.04992721,-0.03070165,0.00445444,-0.04517514,-0.06640445,0.04323801,-0.05377191,-0.03471050,-0.02883901,-0.08168209,0.01126777,-0.02717078,0.04603432,0.02630574,-0.03057331,-0.04654268,-0.03576170,0.02492419,-0.08012348,0.06347644,0.03498705,0.00679496,-0.04286020,0.04106031,0.00546780,-0.05248850,-0.05198993,0.00717061,-0.08126168,0.10924379,0.06609364,-0.13227607,0.05437722,-0.01851338,0.02053592,-0.04329586,0.03116816,0.05851066,-0.06302918,0.08042699,-0.03823515,-0.00852125,0.02583290,0.10453104,0.10736989,-0.03683932,0.02461490,-0.07414632,0.02214347,-0.01734959,-0.03387057,-0.01870336,0.03560610,-0.05922487,-0.02970578,0.04060281,-0.02562548,-0.04360317,0.03394053,-0.01228390,0.00133685,0.03016188,0.06047587,0.02952821,-0.00676782,-0.04554715,-0.06614174,0.02808871,-0.08131392,-0.00217880,0.05443871,0.04878255,-0.02375689,0.05998755,0.06094016,0.09538370,-0.03680045,0.05984521,-0.09019107,0.02912290,-0.00509908,-0.05059129,-0.04763928,-0.00000000,0.05125675,0.04800243,-0.03653439,0.05428017,0.10747702,-0.02086084,0.06900553,0.03001097,-0.02397151,0.02220028,0.03326338,0.00613106,0.00999742,0.09956156,0.13142596,-0.02363803,-0.01661853,0.04194865,0.02937928,0.01756431,0.03250481,-0.01062607,0.03597555,0.01777585,-0.02845441,-0.01727900,-0.02448314,-0.06317102,0.05955921,-0.00716922,0.01172983,0.00386781,-0.06670861,-0.02198587,0.01886145,0.00275950,0.00237464,-0.11707401,0.15151960,0.04079091,-0.08176291,-0.01107548,0.06313650,-0.01936779,-0.00330201,0.01338772,0.00241575,0.04805988,-0.03475891,0.07363129,-0.02767715,0.06442063,0.05166399,-0.04493919,0.00028625,0.01129046,0.02821851,-0.02465949,0.01075248,0.11062849,0.05750740,0.09320379,-0.01813420,-0.02915478,-0.10142489,0.00216380,0.02363506,0.03086909,0.12824769,-0.03358898,-0.07249480,-0.02301600,-0.02137163,-0.02617143,-0.06240339,0.04899856,-0.03557414,-0.08070093,-0.00430113,0.06173460,-0.00237327,0.02605366,-0.04548690,-0.03064057,0.04537338,-0.00107185,-0.00133756,-0.04073842,0.05371899,0.02018989,-0.01051449,-0.08060159,-0.00915920,-0.00779709,-0.05378254,0.00000000,-0.04740298,0.00128834,-0.09815022,0.06708972,-0.06427816,-0.00031879,0.05877111,-0.08499965,-0.01207193,0.02549683,-0.05810383,0.01264257,-0.03316584,0.02223834,0.02615417,-0.06598081,-0.10974941,0.06190979,-0.01037739,-0.00139475,-0.03564746,0.02910594,-0.06146329,-0.00159406,0.08882769,-0.02167082,-0.07998767,-0.02846989,-0.05629042,0.05671238,0.00866754,0.02549884,0.00405961,0.00475579,0.04311059,0.00558751,0.06072630,-0.02367607,-0.02532068,0.01368845,0.10012943,-0.04819214,0.06048900,0.06260734,-0.03735195,0.02644086,-0.09595688,0.01524866,0.01798646,0.01919192,0.04496978,-0.05205785,0.05865905,-0.03376106,-0.04202598,-0.00031995,0.04426628,-0.11047959,0.02238032,-0.05094999,0.00417188,-0.05266488,0.09126493,0.04220546,-0.01660020,-0.04153558,-0.00575638,0.03282002,-0.10978152,-0.08561839,0.05212196,0.04054172,-0.01343855,-0.02822685,-0.10527165,0.03503807,-0.01278448,0.00550598,-0.11148937,0.04499294,-0.05338181,-0.02297504,-0.02276639,0.03747020,-0.10481750,0.06657457,0.02934232,-0.03031552,-0.00471333,-0.07214422,-0.08387364,0.03022792,0.01100212,0.04353725,-0.05360982,-0.00000002,-0.05589062,-0.07888712,-0.01084298,-0.00216171,0.03401057,0.07739305,-0.00796269,-0.07233492,-0.01525981,0.05183464,0.03480596,-0.06177237,-0.00386781,-0.05081845,0.11652093,0.01826838,0.09875327,0.00021589,-0.02002533,-0.00164886,0.12591112,0.00949476,-0.06292765,0.09662142,-0.04693783,-0.02438180,0.03778913,0.07782299,0.01281774,0.02075800,0.00380438,-0.02114513,0.05043268,-0.01083207,0.03183926,-0.03142013,0.08262035,-0.01677570,0.00157804,-0.01472910,-0.05678605,0.07026062,0.04557424,0.01066036,0.08743322,-0.03004136,-0.01306000,-0.02881282,0.00753928,-0.04202509,-0.03684411,0.04318910,-0.02077135,0.03793426,0.00462375,-0.01398493,-0.07219595,-0.03985947,-0.07733785,0.10167962,-0.00930408,0.06239325,0.02543286,-0.01286201]'),
('DIGCOMP_3_4','Programming','DigComp 2.2 competence 3.4: Programming.','Programming (DigComp Competence)','digital','[-0.04735334,-0.02896587,0.00031913,-0.01725142,-0.09446277,-0.05433863,0.05346785,0.07313225,-0.10280201,-0.00568596,-0.06477345,-0.01877026,0.02626561,-0.01529950,0.01712804,-0.00035034,-0.01910631,-0.00231593,0.05502914,-0.05516283,-0.02336640,0.02222291,-0.02439506,-0.08414748,0.02294813,0.04570472,-0.00237116,-0.00320150,0.03893899,-0.01300559,-0.01122727,0.11020041,-0.00090511,0.03506262,0.07093081,0.07835800,-0.00707971,-0.04644668,-0.04821743,0.00767532,-0.04955461,0.00416071,-0.03318378,-0.01285127,0.02066594,0.01375119,-0.01856275,-0.03280606,-0.09407948,-0.01627118,-0.12763041,0.02409606,-0.00087251,-0.06371234,0.01865833,0.01303119,0.11134078,-0.05106986,-0.06024399,-0.04519875,-0.05622824,0.00288426,-0.08249360,0.05695756,0.03145282,0.01432748,0.00580207,0.00899149,0.03000044,-0.01490587,-0.07208658,-0.01383014,-0.03362022,0.07492916,0.04766941,-0.10082840,0.04539514,-0.03299270,0.09284801,-0.09010586,0.02933072,0.13764034,-0.06189956,0.10483819,-0.05191936,-0.00886935,-0.00004145,0.04168549,0.00317131,-0.00702484,-0.00203613,-0.06374038,0.06055475,0.06045381,0.00579451,-0.00906377,-0.03583509,-0.04998486,-0.00651199,0.00319728,-0.04410262,0.04426039,-0.04710990,-0.09182502,-0.06616524,0.00154850,0.06481070,0.01897878,0.06337459,-0.01135001,-0.00820559,0.00394659,-0.00611440,-0.01334526,0.00750952,0.07619732,-0.02122821,0.00556478,0.03664783,0.06376772,0.03562412,0.00285764,-0.03037585,-0.01529724,-0.01715737,-0.11754100,-0.03879072,-0.00000000,0.00889525,0.01869598,-0.01269854,0.03484345,0.03027475,-0.02849746,0.03398905,0.06423260,-0.13421302,0.05913327,-0.02832430,-0.02033464,-0.03665499,0.08524018,-0.00171431,-0.01123199,-0.03672257,0.09175928,-0.00378723,0.00994426,0.03939920,0.04712391,0.03386855,-0.01114414,0.07723301,0.02184273,-0.00561757,-0.00447117,0.11872144,0.00601681,0.02036516,-0.03293693,-0.07516644,0.01569792,0.08364137,0.01867728,0.00553065,-0.05756093,0.05341878,-0.03432321,-0.00819717,0.04090449,0.05495079,-0.01934044,0.08102637,0.02255926,0.00216691,-0.02017062,-0.08013538,0.05279285,0.01303348,0.02478500,0.10687681,-0.05164237,0.05227453,-0.07000341,-0.00111826,0.01180505,0.00889893,0.08214092,0.02339365,0.03872357,-0.03764664,-0.04559026,-0.01411738,0.05790091,-0.01374501,-0.01333719,0.12730716,0.00727807,-0.01995829,0.03920548,-0.05520672,-0.00135779,-0.03993623,-0.06485157,-0.02915617,-0.02796156,0.01144692,0.02906213,-0.01653522,-0.00254781,-0.04989092,-0.03818114,0.06567433,-0.04873927,0.04953874,-0.02266708,-0.00202558,0.04031068,0.03250510,0.01001384,-0.01945871,0.03186797,0.02722828,0.00000000,0.01156649,0.03347893,-0.11836544,0.12221504,-0.02553482,-0.02744318,0.06172254,-0.06429533,-0.03002623,0.02306099,0.00653967,-0.06299916,0.07697271,-0.04077378,0.01569813,0.00004741,-0.08910644,-0.02177652,-0.06195875,0.08462186,-0.00238134,0.00194615,-0.15590514,0.03252825,0.02890828,0.00531752,-0.06270618,0.01192644,0.01177792,0.03542421,0.05059328,-0.01273814,-0.15807627,0.00263650,0.03604084,-0.01760452,0.03632984,-0.00742752,-0.03218785,0.05631085,0.07703867,-0.02455121,0.00296191,0.12675244,-0.02675276,-0.02849012,-0.01143948,-0.01846804,0.02369770,-0.07391652,0.04889768,-0.07095334,0.03613681,-0.04077114,0.01715454,0.08486380,0.03724395,-0.07413419,-0.04215355,0.01272755,0.01586591,-0.03169955,0.01967522,0.06309164,-0.02782124,-0.01850037,-0.05044477,0.05892108,-0.06119293,-0.00551359,-0.03056560,0.05921361,0.03431407,-0.11839468,-0.08089817,0.01286466,-0.04091916,0.04886951,-0.05894575,0.07259975,0.03462953,-0.02465387,0.00996305,0.10220446,-0.07096908,0.09926943,0.06712713,0.04437947,-0.05090334,-0.05211407,-0.05063480,0.04025016,-0.00694596,0.00650306,-0.04709267,-0.00000002,-0.01365342,-0.02201293,-0.00295688,-0.01334185,-0.00514974,0.08155093,-0.05964578,-0.04369856,-0.03935337,0.08731632,0.02192062,-0.03787120,-0.05519846,-0.02834638,0.16261177,0.03762704,0.06671651,0.03101615,-0.01268902,-0.00654089,0.09443664,0.02095487,-0.05735996,0.11504164,-0.07578238,-0.06396171,-0.00934722,-0.03362272,0.06121420,-0.01085651,0.00971985,0.01385211,0.03344126,-0.05875995,0.06144356,-0.01828119,0.04029573,-0.01400449,0.02943711,-0.07667457,-0.01824270,0.05258319,-0.03806832,0.01416036,0.01277378,-0.00970451,0.03353005,-0.06050019,-0.05379500,-0.02158263,-0.05442565,0.01491602,-0.03947902,0.02697800,0.07156213,0.07122665,-0.06164037,-0.03225749,-0.09463099,0.06354877,-0.05718812,0.07619987,0.01525887,0.04180349]');
CREATE TEMP TABLE fix_alias_remove(skill_id text, alias text, reason text, PRIMARY KEY(skill_id,alias)) ON COMMIT DROP;
CREATE TEMP TABLE fix_expected(table_name text PRIMARY KEY, row_count bigint, row_hash text) ON COMMIT DROP;
CREATE TEMP TABLE fix_mapping(role_id text PRIMARY KEY, esco_code text, mapping_relation text,
 mapping_confidence text, approved boolean, review_status text) ON COMMIT DROP;
INSERT INTO fix_mapping VALUES
('M112104','1330.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121104','1211.1.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M121106','2412.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M121107','3312.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M121108','1346.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121109','2412.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121114','2411.1.12','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121115','1346.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121123','2120.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121205','1213.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M121411','1324.8','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M121416','1330.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M122301','1223.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M131102','1311.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M131106','6130.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M131111','1120.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M131114','6113.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M131202','1312.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M131203','1312.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M132101','1321.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M132102','1321.2.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132104','3123.1.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M132105','1349.12','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M132108','1321.2.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132109','1321.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M132110','7212.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132111','1321.2.1.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132112','1321.2.1.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132126','1219.5.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132201','1322.1.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132203','1322.1.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132207','1322.1.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132210','1321.2.1.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132301','1323.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M132310','1323.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132311','2165.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132401','1324.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132402','1324.3.1.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132405','1324.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132414','1324.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M132416','1324.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151101','1330.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M151102','1330.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M151103','2529.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151106','1330.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151108','1330.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M151112','1330.5.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151113','1330.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151116','1330.9','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151117','1330.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151119','2654.1.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M151122','1330.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151123','1330.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151124','1330.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M151127','2131.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151128','2431.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151130','1330.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151132','2434.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M151135','1330.5.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M161202','2221.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M161210','1223.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M161211','3253.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M211101','2111.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M211129','3153.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M211201','2112.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M211202','2112.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M211210','2112.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M211211','2112.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M211302','2113.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M211402','2114.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M211424','2114.1.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M211432','2114.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M212101','2120.6','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M212102','2120.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M212106','2120.6','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M212112','2120.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M212113','2120.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M212115','2112.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213101','2133.9','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213103','2131.4.10','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213104','2131.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213108','2131.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213117','2269.13.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M213120','2131.4.6','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213151','2133.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213169','6112.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213202','2132.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M213203','2132.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M213204','2164.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213205','2132.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M213209','2132.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M213210','2132.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M213214','1312.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213301','3257.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M213302','2132.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213304','2132.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213305','6113.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M213306','2131.4.6.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M213315','2149.11.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M213316','2250.9','partial_proxy','low',false,'pending_low_confidence_review'),
('M213317','2133.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213318','2133.9','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213322','2133.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213402','2131.4.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M213409','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213410','2131.4.11','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213416','2131.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213422','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213433','2131.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M213435','6123.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M213436','2131.4.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M214101','2141.4.2.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214102','2149.15','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214103','2141.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214106','1222.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M214110','2141.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214111','2149.2.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214115','2411.1.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M214120','2149.11','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214142','2149.12.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214144','2141.4.2.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214155','2149.9','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214156','2149.9.7','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214157','2143.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214159','3112.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214169','2149.11','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214202','2142.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214206','2142.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214207','2142.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214238','2142.1.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M214245','2149.14','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214246','3315.8','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214248','2149.14','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214301','2143.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214305','2133.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214402','2144.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214404','7412.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M214413','2144.1.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214436','2144.1.23','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214443','2144.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214458','3119.2.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214459','2144.1.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214503','2145.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214601','2146.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M214606','2146.10','partial_proxy','low',false,'pending_low_confidence_review'),
('M214609','2146.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214616','2146.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214624','4323.19','partial_proxy','low',false,'pending_low_confidence_review'),
('M214641','2144.1.7','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214642','2142.1.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M214645','2142.1.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M214648','2142.1.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M214649','2146.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214901','2146.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M214902','2144.1.10','partial_proxy','low',false,'pending_low_confidence_review'),
('M214907','2149.10','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M214913','2144.1.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M214918','2149.2.8','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214919','2149.5.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214920','2149.12','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M214921','2149.2.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M214922','3257.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M214923','2149.6','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M215102','2151.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M215135','3112.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M215136','3123.1.11','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M215202','2152.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M215236','2152.1.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M215301','2153.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M215323','2523.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M215330','2149.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M216101','2161.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M216102','2161.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M216201','2162.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M216202','2162.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M216301','2163.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M216326','2143.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M216401','2164.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M216402','2164.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M216404','2164.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M216407','2164.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M216501','2165.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M216502','2165.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M216503','2165.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M216507','2165.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M216601','2166.9','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217102','2144.1.10','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M217105','2144.1.14','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M217201','3115.1.9','partial_proxy','low',false,'pending_low_confidence_review'),
('M217203','3152.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M217205','4323.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M217207','3152.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217210','3152.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217211','3331.2.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M217301','3154.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217302','3154.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217303','3153.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M217305','3153.2.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M217310','2144.1.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217311','2144.1.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217312','3154.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217313','3154.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217314','3154.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217315','3154.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217322','3154.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M217401','3154.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217402','3154.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M217403','3154.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M217501','1324.3.1.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M218101','1322.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M218201','1321.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M218202','1219.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M218207','1324.3.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M218229','1349.21','partial_proxy','low',false,'pending_low_confidence_review'),
('M218231','2149.11','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M218301','1323.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221101','2211.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221102','2211.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221107','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221108','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221110','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221111','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221112','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221113','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221118','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221120','2211.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221201','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221204','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221206','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221208','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221209','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221210','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221211','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221213','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221217','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221233','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221234','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221236','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221244','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221257','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221262','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221263','2212.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M221266','3114.1.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M222101','2221.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M222102','2221.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M222109','2221.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M222110','2310.1.28','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M222201','2222.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M224101','3258.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M225101','2250.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M225102','2250.6','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226101','2261.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M226102','2261.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226201','2262.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M226202','2262.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M226207','2262.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M226301','3257.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226320','2263.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226324','3257.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M226325','2133.14','partial_proxy','low',false,'pending_low_confidence_review'),
('M226327','3257.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226328','1321.2.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226329','3112.1.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226331','2263.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M226337','2145.1.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M226341','2143.1.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226344','2149.10','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226401','2264.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M226411','2264.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M226501','2265.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226502','2265.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226514','1321.2.1.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M226601','2266.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226602','2266.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226603','2266.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226701','2267.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M226702','2267.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M226703','3254.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M226801','2269.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M226901','2269.8','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M226902','2320.1.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M231105','2310.1.12','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M231117','2310.1.31','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M232102','2320.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238101','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238102','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238103','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238106','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238107','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238108','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238109','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238110','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238111','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M238112','2320.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M239303','2356.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M242103','2120.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M242401','2424.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M242601','1223.2.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M242602','1349.17','partial_proxy','low',false,'pending_low_confidence_review'),
('M242603','2131.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M242604','2131.4.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M242609','1223.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M242613','1223.2.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M243114','2433.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M243132','2433.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M243301','2433.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M243401','2434.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M243410','2514.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251101','2511.13','partial_proxy','low',false,'pending_low_confidence_review'),
('M251116','2512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251142','2152.1.7.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251144','2511.14','partial_proxy','low',false,'pending_low_confidence_review'),
('M251201','2512.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M251219','2511.14','partial_proxy','low',false,'pending_low_confidence_review'),
('M251243','2522.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251301','2513.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251302','2513.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251401','2512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251407','2511.15','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251419','2512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251433','2522.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251434','2512.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M251902','2519.7.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M251916','2511.18','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252101','2521.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252103','2521.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M252108','2521.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252201','2511.13','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252205','2522.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252208','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252214','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252215','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252222','2512.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M252238','2165.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M252311','2522.1.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252401','2511.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M252403','2511.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M252406','2521.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252411','2511.11','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M252413','2511.11','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M253102','2529.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M253103','2529.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M253120','2529.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M253130','2529.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M253131','2519.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M253136','2529.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M253139','2513.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M254110','2166.13','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254112','2641.4.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M254116','2166.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M254120','2166.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254126','2166.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254127','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254128','2641.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254201','2166.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M254203','2519.7.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M254204','1223.2.1.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254206','2166.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M254209','2166.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254210','2166.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M254211','2654.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M254215','2513.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M254217','2166.9','partial_proxy','low',false,'pending_low_confidence_review'),
('M254301','2166.15','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M254302','2166.9','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M254305','2166.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254314','2513.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M254316','2166.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254317','2431.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M254318','2166.3.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M261907','2619.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M282203','2632.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M282204','2632.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M282206','2632.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M282404','2634.2.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M282407','2634.2.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M291603','2423.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M291608','5419.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M311101','3141.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311102','2310.1.41','partial_proxy','low',false,'pending_low_confidence_review'),
('M311105','3111.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M311106','3111.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311107','3111.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M311108','3111.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M311110','3111.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311112','3111.14','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311114','3111.8','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311116','3111.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311120','3111.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M311125','3111.8','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311132','3141.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311133','3111.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M311136','3141.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311137','2310.1.41','partial_proxy','low',false,'pending_low_confidence_review'),
('M311202','3112.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311204','2149.14','partial_proxy','low',false,'pending_low_confidence_review'),
('M311208','3118.3.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311209','3123.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311210','8113.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M311211','3112.1.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311212','3117.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311213','3112.1.6','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311214','3112.10','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311217','3114.1.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311219','3112.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M311225','3112.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M311226','3115.1.16','partial_proxy','low',false,'pending_low_confidence_review'),
('M311227','5153.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311230','3115.1.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M311232','2149.14','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311233','2149.14','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311237','3315.8','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311301','3113.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311307','3123.1.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M311310','2421.1.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311314','3113.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311315','3114.1.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M311316','3113.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311401','3114.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311402','2421.1.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311404','3114.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311504','3115.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311514','3112.8','partial_proxy','low',false,'pending_low_confidence_review'),
('M311515','2421.1.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311516','4323.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M311517','4323.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M311521','7233.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M311524','3115.1.11','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311527','7223.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M311528','7212.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311529','3117.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M311531','3257.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M311538','3118.3.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311544','3118.3.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311548','7233.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311549','2144.1.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M311550','2144.1.23','partial_proxy','low',false,'pending_low_confidence_review'),
('M311552','3257.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M311601','3116.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311604','3134.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M311605','3116.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311609','2421.1.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311701','3117.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311704','3117.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M311711','9311.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M311723','3112.8','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311801','3118.3.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M311803','3118.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311824','2165.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M311826','2161.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311827','3118.3.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311828','2162.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311829','2164.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M311830','4312.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M311831','3112.10','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311903','7233.7','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311910','3115.1.16','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311928','3119.16','partial_proxy','low',false,'pending_low_confidence_review'),
('M311929','3257.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M311943','3119.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M311944','7223.4.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M311945','3141.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M311948','3119.16','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312201','3122.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312203','3122.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312205','3122.4.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312207','3122.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312209','3122.4.16','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312210','3122.4.16','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312215','1321.2.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M312218','3122.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M312220','2263.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M312226','3115.1.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M312228','7511.6.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M312229','1324.3.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M312234','3139.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M312301','3123.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M312303','3123.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M313104','3131.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M313106','7213.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M313110','3131.3.8','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M313111','3131.3.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M313113','3131.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M313116','7411.1.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M313201','3131.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M313302','3122.4.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M313406','3134.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M313412','3134.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M313417','3134.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M313503','3135.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314101','3141.2.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M314102','3141.2.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314104','3141.2.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M314107','3240.2.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M314109','3141.2.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314203','3111.14','partial_proxy','low',false,'pending_low_confidence_review'),
('M314205','3142.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M314209','7126.6','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314216','3142.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314217','2164.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M314218','2132.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M314221','6111.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M314302','3143.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M314304','3143.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314305','2133.9','partial_proxy','low',false,'pending_low_confidence_review'),
('M314306','2133.9','partial_proxy','low',false,'pending_low_confidence_review'),
('M314401','6221.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M314402','6221.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M314403','6221.11','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314404','6221.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314405','6221.11','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M314407','2132.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M315101','3155.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M315103','7232.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315107','7232.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315108','7232.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M315114','3115.1.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M315115','3154.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M315116','3154.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315201','3343.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M315202','4323.11','partial_proxy','low',false,'pending_low_confidence_review'),
('M315206','3115.1.7','partial_proxy','low',false,'pending_low_confidence_review'),
('M315208','3115.1.9','partial_proxy','low',false,'pending_low_confidence_review'),
('M315301','3115.1.18','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315306','3112.1.10','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315307','7421.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315406','7231.10','partial_proxy','low',false,'pending_low_confidence_review'),
('M315902','1324.3','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M315904','2133.15','partial_proxy','low',false,'pending_low_confidence_review'),
('M316101','3111.10','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M321101','2269.8','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M321102','2269.8','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M321204','2133.15','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M321207','2269.12','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M321208','2269.13.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M321209','2269.13','partial_proxy','low',false,'pending_low_confidence_review'),
('M321212','3212.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M321213','2269.13','partial_proxy','low',false,'pending_low_confidence_review'),
('M321214','3259.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M321301','3213.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M321304','3213.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M321305','3213.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M321401','2261.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M321404','3214.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M321502','2269.15','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M321503','3114.1.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M322101','2221.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M322104','2221.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M324103','3141.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M324107','3240.2.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M324108','3141.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M324109','3240.2.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M324110','3240.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325101','3251.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325105','3251.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325106','2261.3','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M325107','2261.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M325302','3253.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325304','3253.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325305','3253.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325505','3255.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M325506','3255.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325601','3212.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M325602','5321.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325606','2269.8','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325611','2269.8.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325613','2310.1.28','partial_proxy','low',false,'pending_low_confidence_review'),
('M325614','3256.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325615','3258.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M325703','3257.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325705','3257.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M325712','7543.10','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M325735','2133.13','partial_proxy','low',false,'pending_low_confidence_review'),
('M325736','3117.4','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325737','3117.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M325747','3119.5','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325748','3257.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M325749','2133.15','partial_proxy','low',false,'pending_low_confidence_review'),
('M325802','3258.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M325805','3258.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M331401','3314.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M351101','7422.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351105','7422.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351109','3511.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351113','3114.1.6','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351115','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351116','3511.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351123','3522.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351124','2522.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351125','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351201','3512.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351203','3512.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M351206','3512.4','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351207','3513.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351208','2521.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M351209','2514.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M351212','2424.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351213','3511.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M351215','3512.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M351301','3513.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M351303','3512.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M351402','3514.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M352101','3521.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M352102','2654.1.3','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M352105','3435.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M352108','3521.1.10','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M352111','3152.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M352112','3521.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M352116','7422.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M352117','7421.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M352123','3521.1.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M352124','3522.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M352204','7422.7','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M363201','2166.9','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M363202','3432.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M363204','2166.9','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M363221','7317.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M363304','3433.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M363305','4411.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M363306','3433.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M363414','3435.25.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M411126','3343.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M413209','4132.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M422602','4227.2','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431112','3339.2','partial_proxy','low',false,'pending_low_confidence_review'),
('M431114','4312.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431115','4214.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M431118','4311.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M431119','4312.6','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431120','3313.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431123','5230.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431126','4312.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431132','3112.5','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431201','3313.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431203','3314.2','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431215','3313.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431217','4312.2.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431218','4312.4','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M431219','4312.7','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M431220','4312.5','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M431221','3313.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431222','4312.2.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431224','4311.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M431225','4312.2.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M431227','3312.5','partial_proxy','low',false,'pending_low_confidence_review'),
('M431228','3312.6','partial_proxy','low',false,'pending_low_confidence_review'),
('M431231','3314.2','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M431233','3314.1','close_match','high',true,'auto_approved_medium_or_high_test_mapping'),
('M522313','5223.4','partial_proxy','low',false,'pending_low_confidence_review'),
('M531208','2320.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M531210','2320.1','partial_proxy','low',false,'pending_low_confidence_review'),
('M532102','3253.1','broader_proxy','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M818202','8182.1','close_match','medium',true,'auto_approved_medium_or_high_test_mapping'),
('M818209','3131.3','partial_proxy','low',false,'pending_low_confidence_review'),
('M821101','8211.2','partial_proxy','low',false,'pending_low_confidence_review');

DO $guard$
DECLARE t record; n bigint; fp text;
BEGIN
 IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'Wrong database'; END IF;
 IF current_setting('quality_fix.backup_sha256') !~ '^[a-f0-9]{64}$'
    OR current_setting('quality_fix.backup_path') NOT LIKE '/var/lib/postgresql/%/before.dump'
 THEN RAISE EXCEPTION 'A verified persistent backup is required'; END IF;
 IF NOT pg_try_advisory_xact_lock(hashtext('d13_quality_fix_20260830')) THEN RAISE EXCEPTION 'Another quality migration is running'; END IF;
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   EXECUTE format('LOCK TABLE rerouteher.%I IN SHARE ROW EXCLUSIVE MODE', t.tablename);
 END LOOP;
 IF (SELECT count(*) FROM pg_tables WHERE schemaname='rerouteher')<>35
 OR (SELECT count(*) FROM roles)<>665 OR (SELECT count(*) FROM skill_taxonomy)<>6121
 OR (SELECT count(*) FROM role_skills)<>41177 OR (SELECT count(*) FROM role_skill_lineage)<>41194
 OR (SELECT count(*) FROM skill_aliases)<>37730 THEN RAISE EXCEPTION 'Live baseline changed; inspect, do not overwrite'; END IF;
 IF EXISTS(SELECT 1 FROM dataset_metadata WHERE starts_with(metadata_key,'d13_quality_fix_20260830.'))
 THEN RAISE EXCEPTION 'Already applied or prefix in use'; END IF;
 IF NOT EXISTS(SELECT 1 FROM roles WHERE role_id='R01' AND role_title='duplicate' AND masco_code='0' AND esco_code='0')
 OR NOT EXISTS(SELECT 1 FROM roles WHERE role_id='R02' AND role_title='Data Analyst' AND masco_code='2524')
 OR NOT EXISTS(SELECT 1 FROM roles WHERE role_id='R06' AND role_title='Graphic Designer' AND masco_code='2543')
 THEN RAISE EXCEPTION 'Legacy role identity changed'; END IF;
 IF (SELECT count(*) FROM roles WHERE (role_id,role_title,masco_code) IN
   (('M251201','Software Developer','251201'),('M252403','Data Analyst','252403'),('M254302','Graphic Designer','254302')))<>3
 THEN RAISE EXCEPTION 'Canonical MASCO targets do not match reviewed map'; END IF;
 IF (SELECT count(*) FROM fix_mapping WHERE approved)<>442
 OR EXISTS(SELECT 1 FROM fix_mapping m LEFT JOIN roles r USING(role_id) WHERE r.role_id IS NULL OR r.esco_code<>m.esco_code)
 OR EXISTS(SELECT 1 FROM fix_mapping WHERE approved IS DISTINCT FROM (mapping_confidence IN ('medium','high')))
 THEN RAISE EXCEPTION 'Mapping approval rule or live ESCO comparison changed'; END IF;
 IF (SELECT count(*) FROM role_skills WHERE role_id IN ('R01','R02','R06'))<>34
 OR (SELECT count(*) FROM role_skill_lineage WHERE role_id IN ('R01','R02','R06'))<>51
 THEN RAISE EXCEPTION 'Legacy requirement baseline changed'; END IF;
 SELECT md5(string_agg(role_id||'|'||skill_id||'|'||importance::integer::text||';','' ORDER BY role_id COLLATE "C",skill_id COLLATE "C"))
 INTO fp FROM role_skills WHERE role_id ~ '^M[0-9]{6}$';
 IF fp<>'a19a5c3166481a508adc7f7680f4a95c' THEN RAISE EXCEPTION 'D13 requirement pairs differ from reviewed source'; END IF;
 IF EXISTS(SELECT 1 FROM fix_skill_patch p LEFT JOIN skill_taxonomy s USING(skill_id)
  WHERE s.skill_id IS NULL OR s.canonical_name<>p.old_name OR s.definition<>p.old_definition
  OR s.embedding_model<>'sentence-transformers/all-MiniLM-L6-v2')
 THEN RAISE EXCEPTION 'Framework concept definitions changed'; END IF;
 -- Do not silently merge colliding historical records. All target child sets were audited empty.
 FOR t IN SELECT table_name FROM information_schema.columns WHERE table_schema='rerouteher'
   AND column_name='role_id' AND table_name NOT IN ('roles','role_skills','role_skill_lineage') LOOP
   EXECUTE format('SELECT count(*) FROM rerouteher.%I WHERE role_id IN (SELECT new_id FROM fix_role_map)',t.table_name) INTO n;
   IF n<>0 THEN RAISE EXCEPTION 'Historical target collision in %; review manually',t.table_name; END IF;
 END LOOP;
 -- Foreign keys in unexpected schemas would need a separately reviewed migration.
 IF EXISTS(SELECT 1 FROM pg_constraint c JOIN pg_class child ON child.oid=c.conrelid
  WHERE c.contype='f' AND c.confrelid IN ('rerouteher.roles'::regclass,'rerouteher.skill_taxonomy'::regclass)
  AND child.relnamespace<>'rerouteher'::regnamespace) THEN RAISE EXCEPTION 'External schema dependencies found'; END IF;
 SELECT md5(jsonb_build_object(
  'columns',(SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name,ordinal_position) FROM information_schema.columns c WHERE table_schema='rerouteher'),
  'constraints',(SELECT jsonb_agg(jsonb_build_array(conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated) ORDER BY conrelid::regclass::text,conname) FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace),
  'indexes',(SELECT jsonb_agg(to_jsonb(i) ORDER BY tablename,indexname) FROM pg_indexes i WHERE schemaname='rerouteher'),
  'views',(SELECT jsonb_agg(to_jsonb(v) ORDER BY table_name) FROM information_schema.views v WHERE table_schema='rerouteher'),
  'triggers',(SELECT jsonb_agg(jsonb_build_array(tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled) ORDER BY tgrelid::regclass::text,tgname) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='rerouteher'::regnamespace) AND NOT tgisinternal)
 )::text) INTO fp;
 PERFORM set_config('quality_fix.schema_before',fp,true);
END $guard$;

-- Unique canonical labels outrank aliases. Other ambiguous labels are held for review,
-- not resolved to an arbitrary concept. Compute against the POST-PATCH canonical labels.
INSERT INTO fix_alias_remove
WITH canonical AS (
 SELECT s.skill_id,lower(btrim(coalesce(p.canonical_name,s.canonical_name))) term
 FROM skill_taxonomy s LEFT JOIN fix_skill_patch p USING(skill_id)
), terms AS (
 SELECT * FROM canonical UNION SELECT skill_id,lower(btrim(alias)) FROM skill_aliases
), ambiguous AS (
 SELECT term FROM terms GROUP BY term HAVING count(DISTINCT skill_id)>1
)
SELECT a.skill_id,a.alias,
 CASE WHEN EXISTS(SELECT 1 FROM canonical c WHERE c.term=lower(btrim(a.alias)))
 THEN 'Canonical Label Takes Priority' ELSE 'Ambiguous Alias Requires Contextual Review' END
FROM skill_aliases a JOIN ambiguous x ON x.term=lower(btrim(a.alias))
WHERE NOT EXISTS(SELECT 1 FROM canonical c WHERE c.term=x.term AND c.skill_id=a.skill_id);
DO $alias_guard$ BEGIN
 IF (SELECT count(*) FROM fix_alias_remove)<>446
 THEN RAISE EXCEPTION 'Alias review set changed'; END IF;
END $alias_guard$;

-- Archive exact original affected rows and compute expected full-table fingerprints.
-- Historical resume contents stay inside the same database; no content is printed.
DO $archive$
DECLARE t record; pred text; expected_query text; payload jsonb; n bigint; fp text;
BEGIN
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   pred := 'FALSE';
   expected_query := format('SELECT to_jsonb(z) j FROM rerouteher.%I z',t.tablename);
   IF t.tablename='roles' THEN
     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map)';
     expected_query := expected_query || ' WHERE NOT ('||pred||')';
   ELSIF t.tablename='skill_taxonomy' THEN
     pred := 'z.skill_id IN (SELECT skill_id FROM fix_skill_patch)';
     -- The three replacement vectors/names are checked separately after mutation.
     expected_query := expected_query || ' WHERE NOT ('||pred||')';
   ELSIF t.tablename='skill_aliases' THEN
     pred := 'EXISTS(SELECT 1 FROM fix_alias_remove a WHERE a.skill_id=z.skill_id AND a.alias=z.alias)';
     expected_query := expected_query || ' WHERE NOT ('||pred||')';
   ELSIF t.tablename IN ('role_skills','role_skill_lineage') THEN
     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map) OR z.role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved) OR (z.role_id ~ ''^M[0-9]{6}$'' AND z.importance=50) OR z.skill_id IN (SELECT skill_id FROM fix_skill_patch)';
     expected_query := format('SELECT to_jsonb(z) || CASE WHEN p.skill_id IS NOT NULL THEN jsonb_build_object(''skill_name'',p.canonical_name,''skill_type'',p.skill_type) ELSE ''{}''::jsonb END j FROM rerouteher.%I z LEFT JOIN fix_skill_patch p USING(skill_id) WHERE z.role_id NOT IN (SELECT old_id FROM fix_role_map) AND z.role_id NOT IN (SELECT role_id FROM fix_mapping WHERE NOT approved) AND NOT (z.role_id ~ ''^M[0-9]{6}$'' AND z.importance=50)',t.tablename);
   ELSIF t.tablename='dataset_metadata' THEN
     expected_query := expected_query || ' WHERE NOT starts_with(metadata_key,''d13_quality_fix_20260830.'')';
   ELSIF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='rerouteher' AND table_name=t.tablename AND column_name='role_id') THEN
     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map)';
     expected_query := format('SELECT to_jsonb(z) || CASE WHEN m.old_id IS NOT NULL THEN jsonb_build_object(''role_id'',m.new_id) ELSE ''{}''::jsonb END j FROM rerouteher.%I z LEFT JOIN fix_role_map m ON z.role_id=m.old_id',t.tablename);
   END IF;
   EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(z)),''[]''::jsonb) FROM rerouteher.%I z WHERE %s',t.tablename,pred) INTO payload;
   IF jsonb_array_length(payload)>0 THEN
     INSERT INTO dataset_metadata VALUES ('d13_quality_fix_20260830.archive.'||t.tablename,payload);
   END IF;
   EXECUTE 'SELECT count(*),md5(coalesce(string_agg(md5(j::text),'''' ORDER BY md5(j::text)),'''')) FROM ('||expected_query||') q' INTO n,fp;
   INSERT INTO fix_expected VALUES(t.tablename,n,fp);
 END LOOP;
END $archive$;

-- Optional skills are retained as conditional data in the archive and versioned CSV.
-- Essential links are only test core CANDIDATES, not validated MASCO equivalences.
DELETE FROM role_skills WHERE role_id IN (SELECT old_id FROM fix_role_map)
 OR role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved)
 OR (role_id ~ '^M[0-9]{6}$' AND importance=50);
DELETE FROM role_skill_lineage WHERE role_id IN (SELECT old_id FROM fix_role_map)
 OR role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved)
 OR (role_id ~ '^M[0-9]{6}$' AND importance=50);
DELETE FROM skill_aliases a USING fix_alias_remove x WHERE a.skill_id=x.skill_id AND a.alias=x.alias;
UPDATE skill_taxonomy s SET canonical_name=p.canonical_name,skill_type=p.skill_type,embedding=p.embedding_text::vector
 FROM fix_skill_patch p WHERE s.skill_id=p.skill_id;
UPDATE role_skills r SET skill_name=p.canonical_name,skill_type=p.skill_type FROM fix_skill_patch p WHERE r.skill_id=p.skill_id;
UPDATE role_skill_lineage r SET skill_name=p.canonical_name,skill_type=p.skill_type FROM fix_skill_patch p WHERE r.skill_id=p.skill_id;
DO $reparent$
DECLARE t record;
BEGIN
 FOR t IN SELECT table_name FROM information_schema.columns WHERE table_schema='rerouteher' AND column_name='role_id'
 AND table_name NOT IN ('roles','role_skills','role_skill_lineage') ORDER BY table_name LOOP
   EXECUTE format('UPDATE rerouteher.%I z SET role_id=m.new_id FROM fix_role_map m WHERE z.role_id=m.old_id',t.table_name);
 END LOOP;
END $reparent$;
DELETE FROM roles WHERE role_id IN (SELECT old_id FROM fix_role_map);

DO $verify$
DECLARE t record; pred text; n bigint; fp text; schema_fp text;
BEGIN
 FOR t IN SELECT * FROM fix_expected LOOP
   pred := CASE WHEN t.table_name='skill_taxonomy' THEN ' WHERE skill_id NOT IN (SELECT skill_id FROM fix_skill_patch)'
     WHEN t.table_name='dataset_metadata' THEN ' WHERE NOT starts_with(metadata_key,''d13_quality_fix_20260830.'')' ELSE '' END;
   EXECUTE format('SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(z)::text),'''' ORDER BY md5(to_jsonb(z)::text)),'''')) FROM rerouteher.%I z%s',t.table_name,pred) INTO n,fp;
   IF n<>t.row_count OR fp<>t.row_hash THEN RAISE EXCEPTION 'Unexpected data change in %; rolling back',t.table_name; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM fix_skill_patch p JOIN skill_taxonomy s USING(skill_id)
  WHERE s.canonical_name<>p.canonical_name OR s.skill_type<>p.skill_type OR s.definition<>p.old_definition
    OR s.embedding::text<>(p.embedding_text::vector)::text) THEN RAISE EXCEPTION 'Skill patch mismatch'; END IF;
 IF (SELECT count(*) FROM roles)<>662 OR (SELECT count(*) FROM role_skills)<>13266
 OR (SELECT count(*) FROM role_skill_lineage)<>13266 THEN RAISE EXCEPTION 'Incorrect final totals'; END IF;
 IF (SELECT count(*) FROM roles WHERE role_id ~ '^M[0-9]{6}$' AND masco_code ~ '^[0-9]{6}$')<>655
 THEN RAISE EXCEPTION 'MASCO STEM role identities were lost'; END IF;
 IF EXISTS(SELECT 1 FROM roles GROUP BY lower(btrim(role_title)) HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM roles GROUP BY masco_code HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM skill_taxonomy GROUP BY lower(btrim(canonical_name)) HAVING count(*)>1)
 THEN RAISE EXCEPTION 'Duplicate canonical roles/skills remain'; END IF;
 IF EXISTS(SELECT 1 FROM (SELECT skill_id,lower(btrim(canonical_name)) term FROM skill_taxonomy
    UNION SELECT skill_id,lower(btrim(alias)) FROM skill_aliases) x GROUP BY term HAVING count(DISTINCT skill_id)>1)
 THEN RAISE EXCEPTION 'Exact-term alias ambiguity remains'; END IF;
 IF EXISTS(SELECT 1 FROM role_skills r JOIN skill_taxonomy s USING(skill_id) WHERE r.skill_name<>s.canonical_name OR r.skill_type<>s.skill_type)
 THEN RAISE EXCEPTION 'Role-skill labels/types do not match taxonomy'; END IF;
 IF EXISTS(SELECT 1 FROM fix_mapping r WHERE r.approved AND NOT EXISTS(SELECT 1 FROM role_skills s WHERE s.role_id=r.role_id))
 OR EXISTS(SELECT 1 FROM role_skills s JOIN fix_mapping m USING(role_id) WHERE NOT m.approved)
 OR (SELECT count(*) FROM role_skills WHERE role_id='M232102')<>11
 THEN RAISE EXCEPTION 'Core candidate coverage regression'; END IF;
 SELECT md5(jsonb_build_object(
  'columns',(SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name,ordinal_position) FROM information_schema.columns c WHERE table_schema='rerouteher'),
  'constraints',(SELECT jsonb_agg(jsonb_build_array(conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated) ORDER BY conrelid::regclass::text,conname) FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace),
  'indexes',(SELECT jsonb_agg(to_jsonb(i) ORDER BY tablename,indexname) FROM pg_indexes i WHERE schemaname='rerouteher'),
  'views',(SELECT jsonb_agg(to_jsonb(v) ORDER BY table_name) FROM information_schema.views v WHERE table_schema='rerouteher'),
  'triggers',(SELECT jsonb_agg(jsonb_build_array(tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled) ORDER BY tgrelid::regclass::text,tgname) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='rerouteher'::regnamespace) AND NOT tgisinternal)
 )::text) INTO schema_fp;
 IF schema_fp<>current_setting('quality_fix.schema_before') THEN RAISE EXCEPTION 'Permanent schema changed'; END IF;
END $verify$;

INSERT INTO dataset_metadata VALUES
('d13_quality_fix_20260830.policy',jsonb_build_object(
 'version','D13 MASCO2020 Core Candidates v1','test_only',true,'production_ready',false,
 'core_candidate_links',13147,'conditional_links_archived',22203,'low_confidence_essential_links_held',5674,
 'user_authorized_approval_threshold','medium','auto_approved_roles',442,'low_confidence_roles_pending',213,
 'esco_comparisons_preserved',true,'mapping_confidence_and_relation_not_upgraded',true,
 'not_a_validated_readiness_assessment',true,'alias_cache_restart_required',true,
 'remaining_backend_issues',jsonb_build_array('Shared-ESCO LIMIT 1 role lookup','Forced weak recommendations','Missing skill IDs','Empty-band score bias','Stale snapshots'),
 'legacy_group_roles_requiring_review',jsonb_build_array('R03','R04','R05','R07','R08','R09','R10'))),
('d13_quality_fix_20260830.alias_review',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]'::jsonb) FROM fix_alias_remove x)),
('d13_quality_fix_20260830.role_merge_map',(SELECT jsonb_agg(to_jsonb(x)) FROM fix_role_map x)),
('d13_quality_fix_20260830.receipt',jsonb_build_object('applied_at',clock_timestamp(),
 'backup_path',current_setting('quality_fix.backup_path'),'backup_sha256',current_setting('quality_fix.backup_sha256'),
 'schema_signature',current_setting('quality_fix.schema_before'),'schema_changed',false,
 'roles',662,'masco2020_stem_roles',655,'role_skills',13266,'role_skill_lineage',13266,
 'skill_concepts',6121,'skill_ids_merged',0,'archived_alias_rows',(SELECT count(*) FROM fix_alias_remove),
 'historical_reference_rows_preserved',true));
INSERT INTO dataset_metadata(metadata_key,metadata_value)
SELECT 'd13_quality_fix_20260830.mapping.'||m.role_id,
 to_jsonb(m) || jsonb_build_object('reviewer','User-Authorized Automated Confidence Rule',
 'review_date','2026-08-30','use_in_role_skills',m.approved,'production_ready',false,
 'approval_is_not_exact_equivalence',true,'mapping_authority','Project-Derived Test Crosswalk',
 'source_mapping_metadata_key','d13_masco2020_rebuilt_20260830.mapping.'||m.role_id)
FROM fix_mapping m;
\if :fix_commit
COMMIT;
\echo DATA_QUALITY_FIX_COMMITTED
\else
ROLLBACK;
\echo REHEARSAL_PASSED_NO_DATABASE_CHANGES
\endif

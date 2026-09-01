"""Project display Title Case, separate from raw labels and matching aliases.

Capitalize first/last words and principal words. Interior articles, conjunctions
and listed prepositions stay lowercase. Acronyms, units and product spellings
are protected. This transforms display labels only, never codes/URIs/enums.
"""
import re,unicodedata
from collections import Counter,defaultdict

SMALL=set('a an the and as at but by for if in into nor of off on onto or out over per so than till to up upon via vs with yet'.split())
EXPLICIT={x.casefold():x for x in [
    'AI','ICT','IT','NET','MS','JS','GP','GPs','SQL','NoSQL','MySQL','PostgreSQL','JavaScript','TypeScript','HTML','XML','CSS','PHP','JSON','YAML',
    'API','APIs','HTTP','HTTPS','TCP','IP','TCP/IP','DNS','DHCP','VPN','LAN','WAN','WLAN','Wi-Fi','VoIP','SaaS','PaaS','IaaS',
    'IoT','IIoT','CAD','CAM','CAE','CAD/CAM','CNC','PLC','SCADA','HVAC','GIS','GPS','GNSS','BIM','ERP','CRM','SAP',
    'AWS','Azure','DevOps','GitHub','GitLab','PowerShell','PowerPoint','SharePoint','WordPress','AutoCAD','SolidWorks',
    'Excel','Microsoft','Java','Python','MATLAB','SPSS','SAS','BASIC','COBOL','FORTRAN','Linux','Unix','macOS','iOS','Android',
    'C','C++','C#','R','R&D','2D','3D','4D','3-D','2-D','VR','AR','UI','UX','UX/UI','UI/UX','QA','QC',
    'CEO','CFO','CIO','CTO','COO','CISO','HR','HRIS','KPI','KPIs','ISO','IEC','IEEE','CE','EU','UK','US','USA',
    'NHS','WHO','UN','DNA','RNA','PCR','MRI','CT','ECG','EEG','HIV','AIDS','pH','COVID-19','HTML5','CSS3',
    'InDesign','Photoshop','Illustrator','After Effects','YouTube','LinkedIn','Facebook','TikTok','eBay','eHealth',
]}
TOKEN=re.compile(r"[^\W_]+(?:['’][^\W_]+)*(?:\+\+|#)?",re.UNICODE)
AMBIGUOUS={'aids','basic','less','rage','spark','who','it','us','ca','reach'}

def build_protected(records):
    observed=defaultdict(Counter)
    for row in records:
        # Preferred labels are authoritative for product spellings. Alternate
        # label spelling is preserved raw, but does not override preferred case.
        for m in TOKEN.finditer(row['preferredLabel']):
            token=m.group();letters=''.join(c for c in token if c.isalpha())
            if (len(letters)>1 and letters.isupper()) or (any(c.isupper() for c in token[1:]) and any(c.islower() for c in token)):
                observed[token.casefold()][token]+=1
    protected={k:max(counts,key=lambda v:(counts[v],any(c.islower() for c in v),v)) for k,counts in observed.items()}
    protected.update(EXPLICIT)
    return protected

def title_case(text,protected=None):
    protected=protected or EXPLICIT
    # A multiline alternate-label cell contains independent titles. Delimiters
    # and words are retained; only whitespace normalization and case change.
    def segment(s):
        s=' '.join(s.split());matches=list(TOKEN.finditer(s));out=[];cursor=0
        for i,m in enumerate(matches):
            word=m.group();lower=word.casefold()
            boundary=i==0 or i==len(matches)-1 or bool(re.search(r'[:!?]\s*$',s[:m.start()]))
            if lower in SMALL and not boundary:new=lower
            elif lower in protected and (lower not in AMBIGUOUS or word==protected[lower] or word.isupper()):new=protected[lower]
            elif lower.endswith(("'s",'’s')) and lower[:-2] in protected:new=protected[lower[:-2]]+word[-2:].lower()
            elif len(''.join(c for c in word if c.isalpha()))>1 and word.isupper():new=word
            elif any(c.isupper() for c in word[1:]) and any(c.islower() for c in word):new=word
            else:new=word[:1].upper()+word[1:].lower()
            out.extend([s[cursor:m.start()],new]);cursor=m.end()
        out.append(s[cursor:]);result=''.join(out)
        result=re.sub(r'\bt-sne\b','t-SNE',result,flags=re.I)
        return result
    # Keep the source separator spacing: a joined comparison cell may use
    # "title;title", while a prose alias can legitimately use "title; title".
    return '\n'.join(''.join(part if i % 2 else segment(part)
        for i,part in enumerate(re.split(r'(;[ \t]*)',line)))
        for line in str(text).splitlines())

def match_alias(text):
    return ' '.join(unicodedata.normalize('NFKC',text).split()).lower()

TESTS={
    'chief information officer':'Chief Information Officer',
    'use spreadsheets software':'Use Spreadsheets Software',
    'manage health and safety standards':'Manage Health and Safety Standards',
    'ICT system administrator':'ICT System Administrator',
    'use SQL and JavaScript':'Use SQL and JavaScript',
    'use Microsoft Excel':'Use Microsoft Excel',
    '3D animation and CAD/CAM':'3D Animation and CAD/CAM',
    'perform pH measurements':'Perform pH Measurements',
    "assess patient's needs":"Assess Patient's Needs",
    'use .NET and C++':'Use .NET and C++',
    'develop NoSQL databases':'Develop NoSQL Databases',
    'for the benefit of':'For the Benefit Of',
    'data-driven decision-making':'Data-Driven Decision-Making',
    'use visual aids':'Use Visual Aids',
    'provide basic care':'Provide Basic Care',
    'support people who need it':'Support People Who Need It',
    'HIV and AIDS':'HIV and AIDS',
    'less noise and spark detection':'Less Noise and Spark Detection',
    'use JS in MS Excel':'Use JS in MS Excel',
    'comply with ATC instructions':'Comply with ATC Instructions',
    'use IntelliJ IDEA and t-SNE':'Use IntelliJ IDEA and t-SNE',
}

def self_test(protected=None):
    for before,expected in TESTS.items():
        actual=title_case(before,protected)
        assert actual==expected,(before,expected,actual)
        assert title_case(actual,protected)==actual,actual
    return len(TESTS)

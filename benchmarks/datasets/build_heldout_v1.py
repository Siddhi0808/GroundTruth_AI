"""Builds benchmarks/datasets/heldout_v1.json.

Cases were hand-written (not template-generated) from CORE FACT lines in the long_* documents,
using phrasings and perturbations that are independent of scripts/generate_1000_benchmark.py.
They were written BEFORE any rule-engine changes were evaluated on them and must never be used for tuning.
"""
import glob, json, os, re, sys
from datetime import date
from pypdf import PdfReader

ROOT = sys.argv[1]
DOCS = os.path.join(ROOT, "data", "documents")

facts = {}
for f in glob.glob(os.path.join(DOCS, "long_*.txt")):
    for line in open(f, encoding="utf-8"):
        if "CORE FACT:" in line:
            facts.setdefault(line.split("CORE FACT:", 1)[1].strip(), os.path.basename(f))

def src(prefix):
    hits = [(t, s) for t, s in facts.items() if t.startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    return hits[0][1], hits[0][0]

K = {  # key -> fact prefix
    "antibody": "Antibodies, or immunoglobulins", "aristotle": "Aristotle established the Lyceum",
    "athens": "Classical Athens developed", "hash": "Cryptographic hash functions", "dante": "Dante Alighieri",
    "ecosystem": "Ecosystems consist", "game": "Game theory", "chaucer": "Geoffrey Chaucer",
    "keystone": "Keystone species", "laminar": "Laminar fluid flow", "cervantes": "Miguel de Cervantes",
    "phloem": "Phloem tissue", "plato": "Plato founded", "pubkey": "Public-key asymmetric",
    "ribosome": "Ribosomes are", "pwave": "Seismic P-waves", "swave": "Seismic S-waves", "socrates": "Socrates developed",
    "layers": "The Earth is layered", "navier": "The Navier-Stokes", "reynolds": "The Reynolds number",
    "western": "The Western Front", "ferdinand": "The assassination of Archduke", "celltheory": "The cell theory",
    "cortex": "The cerebral cortex", "geodynamo": "The geomagnetic field", "bilayer": "The phospholipid bilayer",
    "thermohaline": "Thermohaline circulation", "shakespeare": "William Shakespeare", "xylem": "Xylem tissue",
    "co2": "Atmospheric carbon dioxide", "atp": "Cellular respiration", "eniac": "ENIAC", "aes": "The Advanced Encryption",
    "chandra": "The Chandrasekhar limit", "neurons": "The human nervous system", "cmb": "The cosmic microwave",
    "ww1": "World War I was", "versailles": "The Treaty of Versailles", "microchip": "The invention of the silicon",
    "mendel": "Gregor Mendel", "babbage": "Charles Babbage", "milkyway": "The Milky Way", "sun": "The Sun converts",
    "trophic": "Trophic levels", "oceanheat": "Global surface ocean",
}

S = [  # (key, query, response)
    ("antibody", "What shape are antibodies and what do they bind to?", "Antibodies are Y-shaped proteins, also called immunoglobulins, that bind specifically to antigen epitopes on foreign pathogens."),
    ("aristotle", "What school did Aristotle found?", "Aristotle established the Lyceum."),
    ("athens", "Where did direct democracy first develop?", "The first documented direct democracy developed in Classical Athens in the fifth century BC, under Pericles."),
    ("hash", "What properties do cryptographic hash functions have?", "A cryptographic hash function produces a fixed-length, deterministic digest, and inverting it is computationally infeasible."),
    ("dante", "In what language was Dante's Divine Comedy written?", "Dante Alighieri wrote the Divine Comedy in the Italian vernacular of the fourteenth century."),
    ("ecosystem", "What makes up an ecosystem?", "An ecosystem is made of a community of interacting organisms together with their physical, abiotic environment."),
    ("game", "What concept formalizes game theory?", "Game theory studies strategic decision-making and is formalized by the Nash equilibrium."),
    ("chaucer", "What did Chaucer's Canterbury Tales portray?", "Chaucer's Canterbury Tales gave a panoramic portrait of medieval English society."),
    ("keystone", "Why are keystone species important?", "Keystone species have a disproportionately large impact on community biodiversity compared with their abundance."),
    ("laminar", "What is laminar flow?", "Laminar flow consists of smooth, parallel fluid layers with minimal mixing and no chaotic turbulence."),
    ("cervantes", "When was Don Quixote published?", "Cervantes published Don Quixote in two parts, in 1605 and 1615."),
    ("phloem", "How does phloem transport sugars?", "Phloem moves sucrose and other photoassimilates in both directions using pressure-flow bulk transport."),
    ("plato", "What did Plato found?", "Plato founded the Academy in Athens around 387 BC and wrote The Republic."),
    ("pubkey", "When was RSA introduced?", "RSA, which introduced public-key cryptography with linked public and private key pairs, dates to 1977."),
    ("ribosome", "What do ribosomes do?", "Ribosomes translate messenger RNA into polypeptide proteins."),
    ("pwave", "Can P-waves travel through liquids?", "Yes. Seismic P-waves are longitudinal compressional waves that travel through both solid rock and liquid layers."),
    ("swave", "What do S-waves reveal about Earth's core?", "Because S-waves are transverse shear waves that cannot travel through liquids, they show that Earth's outer core is liquid."),
    ("socrates", "What method is Socrates known for?", "Socrates developed the elenctic method, a dialectical style of critical questioning of moral assumptions."),
    ("layers", "What are Earth's layers?", "Earth has a solid silicate crust, a semi-solid mantle, a liquid outer core, and a solid iron-nickel inner core."),
    ("navier", "What do the Navier-Stokes equations describe?", "The Navier-Stokes equations are non-linear partial differential equations that describe the motion of viscous fluids."),
    ("reynolds", "What does the Reynolds number measure?", "The Reynolds number is the dimensionless ratio of inertial forces to viscous forces in a flowing fluid."),
    ("western", "What characterized the Western Front?", "Trench warfare, barbed wire, and poison gas characterized the Western Front."),
    ("ferdinand", "What event precipitated the crisis of 1914?", "The assassination of Archduke Franz Ferdinand in Sarajevo in June 1914 precipitated the crisis."),
    ("celltheory", "What does cell theory state?", "Cell theory states that all living organisms are made of one or more cells, the basic unit of life."),
    ("cortex", "What are the lobes of the cerebral cortex?", "The cerebral cortex has frontal, parietal, temporal, and occipital lobes."),
    ("geodynamo", "What generates Earth's magnetic field?", "Earth's magnetic field comes from a geodynamo driven by convection of liquid iron in the outer core."),
    ("bilayer", "How is the cell membrane structured?", "The cell membrane is a phospholipid bilayer with hydrophilic heads facing outward and hydrophobic fatty acid tails inside."),
    ("thermohaline", "What drives thermohaline circulation?", "Thermohaline circulation is driven by differences in water density, temperature, and salinity."),
    ("shakespeare", "How many plays did Shakespeare write?", "Shakespeare wrote 39 plays and 154 sonnets."),
    ("xylem", "What does xylem transport?", "Xylem carries water and dissolved minerals upward from the roots."),
    ("co2", "How much has atmospheric carbon dioxide risen?", "Atmospheric carbon dioxide has risen from about 280 ppm before industrialization to over 420 ppm today."),
    ("atp", "How much ATP does aerobic respiration yield?", "Aerobic cellular respiration yields roughly 30 to 32 ATP per glucose molecule."),
    ("eniac", "When was ENIAC completed?", "ENIAC was completed in 1945 at the University of Pennsylvania."),
    ("aes", "When was AES established?", "NIST established the Advanced Encryption Standard in 2001, based on the Rijndael cipher."),
    ("chandra", "What is the Chandrasekhar limit?", "The Chandrasekhar limit is about 1.4 solar masses, the maximum mass of a stable white dwarf."),
    ("neurons", "How many neurons are in the human nervous system?", "The human nervous system has about 86 billion neurons."),
    ("cmb", "When did the cosmic microwave background originate?", "The cosmic microwave background dates from about 380,000 years after the Big Bang."),
    ("ww1", "When did World War I take place?", "World War I lasted from July 1914 to November 1918."),
    ("versailles", "When was the Treaty of Versailles signed?", "The Treaty of Versailles was signed in June 1919, ending the war between Germany and the Allies."),
    ("microchip", "When was the silicon microchip invented?", "The silicon microchip was invented in 1958."),
]

I = [  # inversions / negations / direction flips
    ("antibody", "What do antibodies bind to?", "Antibodies are Y-shaped proteins that bind randomly to any molecule rather than to specific antigen epitopes."),
    ("aristotle", "What were Aristotle's contributions?", "Aristotle rejected formal logic and made no contributions to biology."),
    ("athens", "How was Classical Athens governed?", "Classical Athens never practiced direct democracy; it was ruled by an absolute monarch under Pericles."),
    ("hash", "Can cryptographic hashes be inverted?", "Cryptographic hash functions produce variable-length digests that are easy to invert."),
    ("dante", "What language is the Divine Comedy in?", "Dante wrote the Divine Comedy in Latin rather than in the Italian vernacular."),
    ("ecosystem", "What is an ecosystem?", "Ecosystems include only living organisms and exclude the physical abiotic environment."),
    ("game", "What does game theory study?", "Game theory ignores strategic interaction and does not use the Nash equilibrium."),
    ("chaucer", "What did the Canterbury Tales depict?", "The Canterbury Tales portrayed only the royal court and did not depict wider medieval English society."),
    ("keystone", "How much do keystone species affect biodiversity?", "Keystone species have a negligible effect on community biodiversity."),
    ("laminar", "Describe laminar flow.", "Laminar flow is chaotic and turbulent, with intense lateral mixing between layers."),
    ("cervantes", "How was Don Quixote published?", "Don Quixote was published as a single volume and is not considered an early modern novel."),
    ("phloem", "In which direction does phloem move sugar?", "Phloem transports sucrose in only one direction, downward, by capillary action."),
    ("plato", "What did Plato establish?", "Plato never founded a school and did not write The Republic."),
    ("pubkey", "How does public-key cryptography use keys?", "In public-key cryptography the same shared secret key is used for both encryption and decryption."),
    ("ribosome", "What do ribosomes translate?", "Ribosomes translate proteins back into messenger RNA."),
    ("pwave", "Do P-waves pass through liquid?", "Seismic P-waves cannot travel through liquid layers."),
    ("swave", "What do S-waves show about the outer core?", "S-waves travel easily through liquids, showing that Earth's outer core is solid."),
    ("socrates", "What did Socrates teach about questioning?", "Socrates discouraged questioning and taught that moral assumptions should never be examined."),
    ("layers", "Which of Earth's cores is liquid?", "Earth's outer core is solid while the inner core is liquid."),
    ("navier", "What kind of equations are the Navier-Stokes equations?", "The Navier-Stokes equations are simple linear equations that apply only to fluids with no viscosity."),
    ("reynolds", "What ratio does the Reynolds number express?", "The Reynolds number is the ratio of viscous forces to inertial forces."),
    ("western", "What kind of war was fought on the Western Front?", "The Western Front was a fast war of movement with no trench warfare."),
    ("ferdinand", "What happened to Archduke Franz Ferdinand in Sarajevo?", "Archduke Franz Ferdinand survived the attack in Sarajevo, and no assassination took place."),
    ("celltheory", "What does cell theory claim?", "Cell theory holds that many living organisms are not made of cells."),
    ("cortex", "How is the cerebral cortex organized?", "The cerebral cortex has no specialized lobes and is a single uniform region."),
    ("geodynamo", "Where does Earth's magnetic field come from?", "Earth's magnetic field is generated by the solid crust, not by any motion in the outer core."),
    ("bilayer", "Which parts of the membrane bilayer are hydrophobic?", "The cell membrane has hydrophobic outer heads and hydrophilic inner tails."),
    ("thermohaline", "What drives the global ocean conveyor belt?", "Thermohaline circulation is driven by wind alone and does not depend on salinity or temperature."),
    ("shakespeare", "Did Shakespeare write sonnets?", "Shakespeare never wrote any sonnets."),
    ("xylem", "Which way does xylem move water?", "Xylem carries water downward from the leaves to the roots."),
]

E = [  # entity / role / concept swaps
    ("aristotle", "Who established the Lyceum?", "Plato established the Lyceum."),
    ("plato", "Who founded the Academy in Athens?", "Aristotle founded the Academy in Athens around 387 BC and wrote The Republic."),
    ("athens", "Who led Athens when direct democracy developed?", "Classical Athens developed the first documented direct democracy under Julius Caesar."),
    ("dante", "Who wrote the Divine Comedy?", "Geoffrey Chaucer wrote the Divine Comedy in the Italian vernacular."),
    ("chaucer", "Who wrote The Canterbury Tales?", "Dante Alighieri wrote The Canterbury Tales, a portrait of medieval English society."),
    ("cervantes", "Who published Don Quixote?", "William Shakespeare published Don Quixote in 1605 and 1615."),
    ("shakespeare", "Who wrote thirty-nine plays and 154 sonnets?", "Miguel de Cervantes wrote thirty-nine plays and 154 sonnets during the Elizabethan era."),
    ("socrates", "Who developed the elenctic method?", "Aristotle developed the elenctic method of questioning moral assumptions."),
    ("game", "Which concept formalizes game theory?", "Game theory is formalized by the concept of the Chandrasekhar limit."),
    ("phloem", "Which tissue translocates sucrose?", "Xylem tissue translocates sucrose bidirectionally via pressure-flow transport."),
    ("xylem", "Which tissue moves water up from the roots?", "Phloem tissue transports water and minerals upward from the roots through transpirational pull."),
    ("pwave", "Which seismic waves are longitudinal?", "Seismic S-waves are longitudinal compressional waves that travel through both solid rock and liquid layers."),
    ("swave", "Which seismic waves cannot cross liquids?", "Seismic P-waves cannot propagate through liquids, which proves the outer core is liquid."),
    ("ferdinand", "Where was Franz Ferdinand assassinated?", "The assassination of Archduke Franz Ferdinand took place in Vienna in June 1914."),
    ("pubkey", "Who introduced public-key cryptography?", "Public-key cryptography with linked key pairs was introduced by AES in 1977."),
    ("aes", "What cipher does AES use?", "The Advanced Encryption Standard was established by NIST in 2001 using the RSA cipher specification."),
    ("eniac", "Where was ENIAC built?", "ENIAC was completed in 1945 at Harvard University."),
    ("antibody", "What are Y-shaped proteins that bind antigens called?", "Ribosomes, or immunoglobulins, are Y-shaped proteins that bind antigen epitopes."),
    ("ribosome", "What translates messenger RNA?", "Antibodies are the complexes responsible for translating messenger RNA into polypeptide proteins."),
    ("navier", "Which equations describe viscous fluid motion?", "The Maxwell equations are the non-linear partial differential equations describing the motion of viscous fluids."),
    ("geodynamo", "Where is the geodynamo located?", "Earth's geomagnetic field is generated by a geodynamo in the solid silicate mantle."),
    ("versailles", "Which war did the Treaty of Versailles end?", "The Treaty of Versailles, signed in June 1919, ended the war between Russia and the Allied Powers."),
    ("mendel", "Who established the laws of inheritance?", "Charles Darwin established the laws of inheritance through pea plant hybridization experiments in 1865."),
    ("babbage", "Who designed the Analytical Engine?", "Alan Turing designed the mechanical Analytical Engine in the 1830s, with Ada Lovelace writing the first algorithm."),
    ("cortex", "Which brain structure has frontal, parietal, temporal and occipital lobes?", "The cerebellum is divided into frontal, parietal, temporal, and occipital lobes."),
]

N = [  # numeric / quantity perturbations
    ("co2", "What is the current atmospheric CO2 level?", "Atmospheric CO2 has risen from pre-industrial levels of 280 ppm to over 520 ppm today."),
    ("atp", "How many ATP molecules does aerobic respiration produce?", "Aerobic respiration yields approximately 36 to 38 ATP molecules per glucose."),
    ("eniac", "When was ENIAC finished?", "ENIAC was completed in 1949 at the University of Pennsylvania."),
    ("mendel", "When did Mendel publish his inheritance laws?", "Mendel established the laws of inheritance through pea plant experiments in 1856."),
    ("cervantes", "When were the two parts of Don Quixote published?", "Cervantes published Don Quixote in two parts, in 1605 and 1625."),
    ("plato", "When did Plato found the Academy?", "Plato founded the Academy in Athens around 287 BC."),
    ("pubkey", "When did RSA introduce public-key cryptography?", "Public-key cryptography was introduced by RSA in 1987."),
    ("aes", "In which year was AES established?", "NIST established AES in 2011 using the Rijndael cipher."),
    ("chandra", "What is the value of the Chandrasekhar limit?", "The Chandrasekhar limit is approximately 2.4 solar masses."),
    ("milkyway", "How many stars are in the Milky Way?", "The Milky Way contains an estimated 100 to 400 million stars."),
    ("sun", "How much hydrogen does the Sun fuse each second?", "The Sun converts approximately 60 million tons of hydrogen into helium every second."),
    ("versailles", "When was the Treaty of Versailles signed?", "The Treaty of Versailles was signed in June 1918."),
    ("ferdinand", "When was Franz Ferdinand assassinated?", "Franz Ferdinand was assassinated in Sarajevo in June 1915."),
    ("cmb", "How long after the Big Bang did the CMB form?", "The cosmic microwave background dates from approximately 38,000 years after the Big Bang."),
    ("neurons", "How many neurons does the human nervous system contain?", "The human nervous system contains an estimated 68 billion neurons."),
    ("microchip", "When was the silicon microchip invented?", "The silicon microchip was invented in 1968."),
    ("shakespeare", "How many plays did Shakespeare write?", "Shakespeare wrote 37 plays and 154 sonnets."),
    ("ww1", "When did World War I end?", "World War I lasted from July 1914 until November 1919."),
    ("trophic", "How much energy transfers between trophic levels?", "Roughly twenty percent of energy is transferred between adjacent trophic levels."),
    ("oceanheat", "How much excess heat have the oceans absorbed?", "The oceans have absorbed more than fifty percent of the accumulated excess heat."),
    ("co2", "What was the pre-industrial CO2 concentration?", "Carbon dioxide rose from pre-industrial levels of 180 ppm to over 420 ppm."),
    ("milkyway", "Roughly how many stars does our galaxy hold?", "The Milky Way contains an estimated 10 to 40 billion stars."),
    ("cmb", "When was the cosmic microwave background released?", "The cosmic microwave background dates from about 3.8 million years after the Big Bang."),
    ("mendel", "When were Mendel's pea plant experiments?", "Mendel's pea plant experiments established the laws of inheritance in 1765."),
    ("aes", "When did NIST adopt AES?", "AES was established by NIST in 1991."),
]

Z = [  # out-of-corpus: plausible, (mostly) true answers about topics absent from the corpus
    ("Vivaldi", "Who composed The Four Seasons?", "Antonio Vivaldi composed The Four Seasons, a set of violin concertos published in 1725."),
    ("Machu Picchu", "Where is Machu Picchu?", "Machu Picchu is a 15th-century Inca citadel in the Andes mountains of Peru."),
    ("Suez", "When did the Suez Canal open?", "The Suez Canal opened in 1869, linking the Mediterranean Sea to the Red Sea."),
    ("Bitcoin", "Who created Bitcoin?", "Bitcoin was created by the pseudonymous Satoshi Nakamoto, who released its whitepaper in 2008."),
    ("Fuji", "How tall is Mount Fuji?", "Mount Fuji rises 3,776 meters and is the highest mountain in Japan."),
    ("Beethoven", "How many symphonies did Beethoven write?", "Ludwig van Beethoven completed nine symphonies."),
    ("Mandela", "When did Nelson Mandela become president?", "Nelson Mandela became President of South Africa in 1994."),
    ("Angkor", "What is Angkor Wat?", "Angkor Wat is a vast temple complex in Cambodia built in the 12th century."),
    ("Stonehenge", "How old is Stonehenge?", "Stonehenge in England was built in stages beginning around 3000 BC."),
    ("Pisa", "Why does the Tower of Pisa lean?", "The Leaning Tower of Pisa tilts because it was built on soft, unstable soil."),
    ("Kasparov", "Which computer defeated Garry Kasparov?", "IBM's Deep Blue defeated world chess champion Garry Kasparov in 1997."),
    ("Starry Night", "Who painted The Starry Night?", "Vincent van Gogh painted The Starry Night in 1889."),
    ("Sydney Opera", "Who designed the Sydney Opera House?", "Danish architect Jorn Utzon designed the Sydney Opera House, which opened in 1973."),
    ("Mozart", "Which operas did Mozart write?", "Wolfgang Amadeus Mozart composed more than twenty operas, including The Magic Flute."),
    ("Tolkien", "Who wrote The Lord of the Rings?", "J. R. R. Tolkien wrote The Lord of the Rings, published between 1954 and 1955."),
    ("Colosseum", "When was the Colosseum completed?", "The Colosseum in Rome was completed in 80 AD under Emperor Titus."),
    ("Petra", "What is Petra famous for?", "Petra in Jordan is famous for buildings carved into rose-red sandstone cliffs by the Nabataeans."),
    ("Monet", "Who painted the Water Lilies series?", "Claude Monet painted the Water Lilies series of about 250 works."),
    ("Serengeti", "Where is the Serengeti?", "The Serengeti is a savanna ecosystem in Tanzania known for its annual wildebeest migration."),
    ("Yellowstone", "When was Yellowstone established?", "Yellowstone became the world's first national park in 1872."),
    ("Niagara", "How tall is Niagara Falls?", "Horseshoe Falls at Niagara is about 57 meters tall."),
    ("Austen", "Who wrote Pride and Prejudice?", "Jane Austen published Pride and Prejudice in 1813."),
    ("Tokyo", "What was Tokyo's former name?", "Tokyo was formerly known as Edo before 1868."),
    ("Tour de France", "Who won the first Tour de France?", "Maurice Garin won the first Tour de France in 1903."),
    ("Guernica", "Who painted Guernica?", "Pablo Picasso painted Guernica in 1937 in response to the bombing of the Basque town."),
    ("Hemingway", "Who wrote The Old Man and the Sea?", "Ernest Hemingway wrote The Old Man and the Sea, which won the Pulitzer Prize in 1953."),
    ("Victoria Falls", "Where is Victoria Falls?", "Victoria Falls lies on the Zambezi River between Zambia and Zimbabwe."),
    ("Tchaikovsky", "Who composed Swan Lake?", "Pyotr Ilyich Tchaikovsky composed the ballet Swan Lake in 1876."),
    ("Brandenburg", "How many Brandenburg Concertos did Bach write?", "Johann Sebastian Bach wrote six Brandenburg Concertos."),
    ("kangaroo", "Where do kangaroos live?", "Kangaroos are marsupials native to Australia."),
]

# Verify out-of-corpus keywords are absent from the extracted text of every document (incl. PDFs).
corpus = []
for f in os.listdir(DOCS):
    p = os.path.join(DOCS, f)
    if f.endswith(".txt"):
        corpus.append(open(p, encoding="utf-8", errors="replace").read().lower())
    elif f.endswith(".pdf"):
        try:
            corpus.append("\n".join((pg.extract_text() or "") for pg in PdfReader(p).pages).lower())
        except Exception:
            pass
blob = "\n".join(corpus)
for kw, _, _ in Z:
    assert kw.lower() not in blob, f"out-of-corpus keyword present in corpus: {kw}"

cases = []
def add(cat, key, q, r, verdict, three):
    source_doc, fact = src(K[key]) if key in K else (None, None)
    cases.append({"id": len(cases) + 1, "category": cat, "query": q, "response": r,
                  "expected_verdict": verdict, "expected_3way": three,
                  "source_doc": source_doc, "source_fact": fact})

for k, q, r in S: add("Supported", k, q, r, "Supported", "Supported")
for k, q, r in I: add("AdversarialInversion", k, q, r, "Hallucinated", "Hallucinated")
for k, q, r in E: add("EntityRoleSwap", k, q, r, "Hallucinated", "Hallucinated")
for k, q, r in N: add("NumericalPerturbation", k, q, r, "Hallucinated", "Hallucinated")
for kw, q, r in Z: add("ZeroEvidence", kw, q, r, "Hallucinated", "Insufficient Evidence")

assert len({(c["query"], c["response"]) for c in cases}) == len(cases), "duplicate cases"
out = {"name": "heldout_v1", "created": str(date.today()),
       "provenance": "Hand-written by the Claude Code assistant from CORE FACT lines in data/documents/long_*.txt; "
                     "out-of-corpus topics verified absent from extracted corpus text. Written before rule-engine changes "
                     "were evaluated on it. Never used for tuning.",
       "cases": cases}
path = os.path.join(ROOT, "benchmarks", "datasets", "heldout_v1.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(out, open(path, "w"), indent=2)
from collections import Counter
print(len(cases), Counter(c["category"] for c in cases))

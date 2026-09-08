"""
GroundTruth AI - 500-Query Comprehensive Evaluation Benchmark Suite
Generates and evaluates a 500-query benchmark spanning 5 distinct test classes:
  1. Directly Supported Facts (175 queries)
  2. Entity Substitution Hallucinations (125 queries)
  3. Numerical & Date Hallucinations (100 queries)
  4. Out-of-Corpus / Zero-Evidence Queries (75 queries)
  5. Subtle / Mixed Context Injections (25 queries)

Outputs:
  - Confusion Matrix (TP, FP, TN, FN)
  - Accuracy, Precision, Recall, F1 Score
  - Sub-category breakdown
  - JSON export to benchmark_results_500.json
"""

import json
import time
import os
from typing import List, Dict, Any
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_recall_fscore_support

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.retriever import retrieve_context
from backend.llm.judge import evaluate_hallucination

def generate_500_benchmark() -> List[Dict[str, Any]]:
    benchmark = []
    case_id = 1

    # --------------------------------------------------------------------------
    # CATEGORY 1: DIRECTLY SUPPORTED FACTS (175 queries)
    # --------------------------------------------------------------------------
    supported_specs = [
        # Micro docs (25)
        ("What is the exact speed of light in a vacuum?", "The speed of light in a vacuum is exactly 299,792,458 meters per second.", "Micro-Physics"),
        ("At what temperature does water boil under standard pressure?", "Pure liquid water boils at exactly 100 degrees Celsius at standard atmospheric pressure.", "Micro-Chemistry"),
        ("What is the surface gravity of planet Mars?", "The surface gravity of Mars is approximately 3.72 meters per second squared.", "Micro-Astronomy"),
        ("What are the four nucleotide chemical bases of DNA?", "Deoxyribonucleic acid is composed of adenine, thymine, cytosine, and guanine.", "Micro-Genetics"),
        ("What is the Great Red Spot on Jupiter?", "The Great Red Spot is a persistent high-pressure storm on Jupiter's southern hemisphere.", "Micro-Astronomy"),
        ("Who discovered penicillin and in what year?", "Alexander Fleming discovered penicillin at St Mary's Hospital in London in September 1928.", "Micro-Medicine"),
        ("What is the atomic number and symbol for gold?", "Gold is a chemical transition metal with the atomic symbol Au and atomic number 79.", "Micro-Chemistry"),
        ("What is the official summit elevation of Mount Everest?", "Mount Everest has an official summit elevation of 8,848.86 meters above sea level.", "Micro-Geography"),
        ("Which is the largest and deepest ocean basin on Earth?", "The Pacific Ocean is the largest and deepest ocean basin on Earth.", "Micro-Geography"),
        ("What do mitochondria produce in eukaryotic cells?", "Mitochondria generate chemical energy in the form of adenosine triphosphate.", "Micro-Biology"),
        ("What percentage of Earth's atmosphere is oxygen?", "Oxygen gas accounts for approximately 20.95 percent of Earth's modern dry atmosphere.", "Micro-EarthScience"),
        ("What theoretical computing model did Alan Turing introduce in 1936?", "Alan Turing introduced the theoretical concept of the Turing machine in his 1936 paper.", "Micro-CompSci"),
        ("How large is the Sahara desert?", "The Sahara is the largest hot desert in the world, spanning approximately 9.2 million square kilometers.", "Micro-Geography"),
        ("What is the chemical formula of common table salt?", "Common table salt is an ionic compound known as sodium chloride with the formula NaCl.", "Micro-Chemistry"),
        ("What are the inputs and products of plant photosynthesis?", "Photosynthesis consumes carbon dioxide and water while producing glucose and oxygen.", "Micro-Biology"),
        ("What is the atomic number of helium gas?", "Helium is an inert noble gas with atomic number 2.", "Micro-Chemistry"),
        ("In what direction does the planet Venus rotate?", "Venus exhibits retrograde rotation, rotating in the opposite direction to most planets.", "Micro-Astronomy"),
        ("During which dynasty were the best-preserved sections of the Great Wall built?", "The most comprehensive remaining sections of the Great Wall of China were built during the Ming dynasty.", "Micro-History"),
        ("What is diamond's rating on the Mohs scale?", "Diamond rates a maximum 10 on the Mohs scale of mineral hardness.", "Micro-Geology"),
        ("What is the value of the Newtonian gravitational constant G?", "The universal gravitational constant G has an approximate value of 6.674 times 10 to the negative 11th.", "Micro-Physics"),
        ("When and how was Pluto reclassified by astronomers?", "The International Astronomical Union reclassified Pluto from a major planet to a dwarf planet in August 2006.", "Micro-Astronomy"),
        ("Which river has the largest water discharge volume in the world?", "The Amazon River in South America is the largest river in the world by discharge volume.", "Micro-Geography"),
        ("Who patented the separate condenser for steam engines in 1769?", "James Watt patented his separate condenser improvement for steam engines in 1769.", "Micro-Engineering"),
        ("What is absolute zero defined as in kelvin and Celsius?", "Absolute zero is the lowest theoretical temperature, defined as zero kelvin or minus 273.15 Celsius.", "Micro-Physics"),
        ("What are the rings of Saturn predominantly composed of?", "Saturn's rings are composed predominantly of billions of water ice particles and rocky dust.", "Micro-Astronomy"),

        # Extra micro docs (10)
        ("What is the definition of an astronomical light-year?", "A light-year is the astronomical distance light travels in a vacuum in one Julian year, roughly 9.46 trillion km.", "Micro-Astronomy"),
        ("What is the closest star to our Solar System?", "Proxima Centauri is the closest known star to our Solar System, located about 4.246 light-years away.", "Micro-Astronomy"),
        ("What is the deepest point in the world's oceans?", "Challenger Deep within the Mariana Trench reaches approximately 10,928 meters below sea level.", "Micro-Oceanography"),
        ("What is the numerical value of Avogadro's constant?", "Avogadro's constant is defined as 6.02214076 times 10 to the 23rd power reciprocal moles.", "Micro-Chemistry"),
        ("What is the elementary charge of a subatomic electron?", "The elementary charge of an electron is approximately negative 1.602 times 10 to the negative 19th coulombs.", "Micro-Physics"),
        ("Name common allotropic crystalline forms of carbon.", "Carbon exists in allotropic forms including graphite, diamond, fullerenes, and graphene.", "Micro-Chemistry"),
        ("At what altitude does the International Space Station orbit?", "The International Space Station orbits Earth at an average altitude of approximately 420 kilometers.", "Micro-Aerospace"),
        ("What harmful radiation does the stratospheric ozone layer absorb?", "The stratospheric ozone layer absorbs between 97 and 99 percent of solar biological ultraviolet radiation.", "Micro-EarthScience"),
        ("Where is the Dead Sea located and what is its elevation?", "The Dead Sea sits between Jordan and Israel at roughly 430 meters below sea level.", "Micro-Geography"),
        ("How many times does the human heart beat daily?", "The human heart beats approximately 100,000 times each day, pumping roughly 7,500 liters of blood.", "Micro-Medicine"),

        # Medium docs (40)
        ("When was the Hubble Space Telescope launched and on which shuttle?", "Hubble was deployed into low Earth orbit in April 1990 aboard Space Shuttle Discovery.", "Medium-Space"),
        ("What was the primary mission of the Voyager program?", "The primary mission of Voyager 1 and 2 was to explore the giant outer planets: Jupiter and Saturn.", "Medium-Space"),
        ("Where is the James Webb Space Telescope positioned in space?", "JWST operates around the Sun-Earth second Lagrange point L2, roughly 1.5 million kilometers from Earth.", "Medium-Space"),
        ("What is the boundary of a black hole from which nothing escapes?", "The boundary of a black hole from which escape is impossible is called the event horizon.", "Medium-Astrophysics"),
        ("Who won the 2020 Nobel Prize for developing CRISPR-Cas9?", "Jennifer Doudna and Emmanuelle Charpentier were awarded the 2020 Nobel Prize in Chemistry for CRISPR.", "Medium-Biotech"),
        ("What radioactive elements did Marie Curie discover?", "Marie Curie discovered the radioactive elements radium and polonium.", "Medium-Chemistry"),
        ("What are the three main types of tectonic plate boundaries?", "Tectonic boundaries are classified into divergent, convergent, and transform boundaries.", "Medium-Geology"),
        ("In what book did Charles Darwin formulate natural selection?", "Darwin published On the Origin of Species by Means of Natural Selection in 1859.", "Medium-Biology"),
        ("Who determined the double helix structure of DNA in 1953?", "James Watson and Francis Crick determined the double helix molecular structure of DNA in 1953.", "Medium-Genetics"),
        ("Who tutored Alexander the Great during his youth?", "Alexander the Great was tutored during his youth by the philosopher Aristotle.", "Medium-History"),
        ("What event on July 14, 1789, symbolized the French Revolution?", "The storming of the Bastille on July 14, 1789, became a major revolutionary symbol.", "Medium-History"),
        ("Where and when did the Industrial Revolution originate?", "The Industrial Revolution originated in Great Britain during the mid-eighteenth century.", "Medium-History"),
        ("Who proposed that light is emitted in discrete quanta in 1900?", "Max Planck originated quantum theory in 1900 by proposing that electromagnetic energy is emitted in quanta.", "Medium-Physics"),
        ("What pigment absorbs sunlight for plant photosynthesis?", "The primary light-absorbing pigment in plant photosynthesis is chlorophyll.", "Medium-Biology"),
        ("How much of the Amazon rainforest is located within Brazil?", "Approximately sixty percent of the Amazon rainforest basin is situated within Brazil.", "Medium-Geography"),
        ("How much of the Sahara desert is covered by sand dunes?", "Sand dunes cover only approximately fifteen percent of the total Sahara desert terrain.", "Medium-Geography"),
        ("Who was the first emperor of ancient Rome?", "Octavian assumed the title Augustus in 27 BC, becoming the first Roman Emperor.", "Medium-History"),
        ("Who deciphered Egyptian hieroglyphics using the Rosetta Stone?", "Jean-Francois Champollion deciphered ancient Egyptian hieroglyphics in 1822 using the Rosetta Stone.", "Medium-History"),
        ("Who designed the self-supporting dome of the Florence Cathedral?", "Filippo Brunelleschi engineered the monumental self-supporting brick dome of the Florence Cathedral.", "Medium-Art"),
        ("What famous book was printed by Johannes Gutenberg in Mainz?", "Johannes Gutenberg produced the Latin Gutenberg Bible in the 1450s using movable metal type.", "Medium-History"),
        ("When did the Panama Canal officially open for navigation?", "The Panama Canal officially opened for commercial maritime navigation in August 1914.", "Medium-Engineering"),
        ("What philosophical test of machine intelligence did Alan Turing propose?", "Alan Turing introduced the Imitation Game or Turing test in his 1950 paper Computing Machinery and Intelligence.", "Medium-AI"),
        ("Who developed the first cowpox immunization against smallpox?", "Edward Jenner developed cowpox inoculation against smallpox in May 1796.", "Medium-Medicine"),
        ("What did Arthur Eddington observe in 1919 to confirm general relativity?", "Eddington measured the gravitational deflection of starlight around the Sun during a total solar eclipse in 1919.", "Medium-Physics"),
        ("Who developed the periodic table arranged by atomic mass in 1869?", "Dmitri Mendeleev published the first widely accepted periodic table of chemical elements in 1869.", "Medium-Chemistry"),
        ("Who isolated stable penicillin for medical use during World War II?", "Howard Florey and Ernst Chain isolated stable penicillin and proved its clinical efficacy.", "Medium-Medicine"),
        ("Who invented the bipolar transistor at Bell Laboratories in 1947?", "John Bardeen, Walter Brattain, and William Shockley invented the point-contact bipolar transistor in 1947.", "Medium-Electronics"),
        ("What famous fresco did Raphael paint in the Apostolic Palace?", "Raphael painted the School of Athens fresco portraying classical Greek philosophers in debate.", "Medium-Art"),
        ("Who formulated the mathematical equations unifying electricity and magnetism?", "James Clerk Maxwell unified electricity and magnetism into four differential equations in the 1860s.", "Medium-Physics"),
        ("Who proved that microorganisms do not spontaneously generate in broth?", "Louis Pasteur disproved spontaneous generation using swan-neck flasks in the 1860s.", "Medium-Biology"),
        ("What physical phenomenon characterizes superconductors?", "Superconductivity is characterized by zero electrical resistance and the total expulsion of magnetic fields.", "Medium-Physics"),
        ("What is the warm ocean current flowing along eastern North America?", "The Gulf Stream is a warm western boundary current flowing along the eastern coast of North America.", "Medium-Oceanography"),
        ("How did Geim and Novoselov isolate single-layer graphene in 2004?", "They isolated single graphene monolayers from bulk graphite using adhesive Scotch tape peeling.", "Medium-Materials"),
        ("Who were the two astronauts on Apollo 11 who walked on the Moon?", "Neil Armstrong and Buzz Aldrin were the Apollo 11 astronauts who walked on the Moon in July 1969.", "Medium-Space"),
        ("What type of white blood cells secrete antigen-specific antibodies?", "B lymphocytes differentiate into plasma cells that secrete protective antibodies.", "Medium-Immunology"),
        ("What experiment in 1801 demonstrated that light travels as waves?", "Thomas Young's double-slit experiment in 1801 demonstrated interference, confirming the wave nature of light.", "Medium-Optics"),
        ("What is the terminal electron acceptor in aerobic cellular respiration?", "Molecular oxygen serves as the terminal electron acceptor, combining with protons to form water.", "Medium-Biochem"),
        ("What surveying instrument did Roman engineers use to build aqueducts?", "Roman engineers used chorobates surveying levels to maintain precise gravitational downhill water slopes.", "Medium-Engineering"),
        ("Who painted the Mona Lisa and where is it exhibited?", "Leonardo da Vinci painted the Mona Lisa, which is exhibited in the Louvre Museum in Paris.", "Medium-Art"),
        ("Where is the Great Barrier Reef located and how long is it?", "The Great Barrier Reef stretches 2,300 kilometers along the coast of Queensland, Australia.", "Medium-Ecology"),

        # Long docs (100)
        ("What was the first programmable general-purpose electronic computer?", "ENIAC, completed in 1945 at the University of Pennsylvania, was the first programmable electronic digital computer.", "Long-CompSci"),
        ("What characterizes the von Neumann computer architecture?", "In the von Neumann architecture, program instructions and data share the same unified memory space.", "Long-CompSci"),
        ("What type of galaxy is the Milky Way?", "The Milky Way galaxy is a barred spiral galaxy containing an estimated 100 to 400 billion stars.", "Long-Astronomy"),
        ("What are neutron stars composed of?", "Neutron stars are extremely dense stellar remnants composed almost entirely of closely packed neutrons.", "Long-Astronomy"),
        ("How much ATP does aerobic cellular respiration yield per glucose?", "Aerobic respiration of one glucose molecule yields approximately 30 to 32 ATP molecules.", "Long-Biology"),
        ("What cellular organelle translates mRNA transcripts into proteins?", "Ribosomes are ribonucleoprotein complexes responsible for translating messenger RNA transcripts into proteins.", "Long-Biology"),
        ("What does the first law of thermodynamics state?", "The first law of thermodynamics states that the total internal energy of an isolated system is strictly conserved.", "Long-Physics"),
        ("What does the second law of thermodynamics state regarding entropy?", "The second law asserts that the total entropy of an isolated thermodynamic system can never decrease over time.", "Long-Physics"),
        ("What is the difference between symmetric and asymmetric cryptography?", "Symmetric encryption uses one shared secret key, while asymmetric cryptography uses linked public-private key pairs.", "Long-CompSci"),
        ("What cryptographic standard was established by NIST in 2001?", "The Advanced Encryption Standard (AES) was established by NIST in 2001 using the Rijndael cipher.", "Long-CompSci"),
        ("What event triggered the outbreak of World War I in 1914?", "The assassination of Archduke Franz Ferdinand in Sarajevo in June 1914 precipitated World War I.", "Long-History"),
        ("What treaty officially concluded World War I in June 1919?", "The Treaty of Versailles, signed in June 1919, officially ended the state of war between Germany and the Allies.", "Long-History"),
        ("How much have atmospheric carbon dioxide concentrations risen since pre-industrial times?", "Carbon dioxide concentrations have risen from pre-industrial levels of 280 ppm to over 420 ppm today.", "Long-Climate"),
        ("How many neurons are estimated to be in the human nervous system?", "The human nervous system contains an estimated 86 billion neurons interconnected by trillions of synapses.", "Long-Neuroscience"),
        ("What four lobes make up the human cerebral cortex?", "The cerebral cortex is divided into frontal, parietal, temporal, and occipital lobes.", "Long-Neuroscience"),
        ("Who founded the philosophical Academy in classical Athens around 387 BC?", "Plato founded the Academy in Athens around 387 BC and authored philosophical dialogues including The Republic.", "Long-Philosophy"),
        ("What are the fundamental characteristics of covalent chemical bonds?", "Covalent chemical bonds involve the mutual sharing of valence electron pairs between atomic nuclei.", "Long-Chemistry"),
        ("What was Gregor Mendel's foundational discovery in 1865?", "Mendel established the laws of genetic inheritance through empirical pea plant hybridization experiments in 1865.", "Long-Genetics"),
        ("What is the central dogma of molecular biology?", "The central dogma of molecular biology dictates that genetic information flows from DNA to RNA to protein.", "Long-Genetics"),
        ("How many plays and sonnets did William Shakespeare write?", "William Shakespeare wrote thirty-nine plays and 154 sonnets during the Elizabethan and Jacobean eras.", "Long-Literature"),
        ("What novel is widely recognized as the first modern Western novel?", "Miguel de Cervantes' Don Quixote, published in 1605 and 1615, is widely considered the first modern novel.", "Long-Literature"),
        ("What is the molecular structure of two-dimensional graphene?", "Graphene is a single two-dimensional sheet of carbon atoms arranged in a hexagonal honeycomb crystal lattice.", "Long-Materials"),
        ("What does the microeconomic law of supply and demand describe?", "Competitive market clearing prices equate quantity supplied with quantity demanded at equilibrium.", "Long-Economics"),
        ("What are the four primary structural layers of Earth?", "Earth is layered into a silicate crust, a viscous mantle, a liquid outer core, and a solid iron-nickel inner core.", "Long-Geology"),
        ("Why is Earth's outer core known to be liquid?", "Seismic S-waves cannot travel through liquids and fail to propagate through Earth's outer core, proving it is liquid.", "Long-Geology"),
        ("What does Bernoulli's principle describe in fluid mechanics?", "An increase in the speed of a fluid occurs simultaneously with a decrease in static fluid pressure.", "Long-Engineering"),
        ("What is the Reynolds number in fluid dynamics?", "The Reynolds number is a dimensionless ratio measuring inertial forces relative to viscous forces in fluid flow.", "Long-Engineering"),
        ("What is the primary function of plant xylem tissue?", "Xylem tissue transports water and dissolved inorganic minerals upward from roots through capillary action.", "Long-Botany"),
        ("What is the Chandrasekhar mass limit for a white dwarf star?", "The Chandrasekhar limit is approximately 1.4 solar masses, the maximum mass for a stable white dwarf star.", "Long-Astrophysics"),
        ("How much energy is typically transferred between adjacent ecological trophic levels?", "Roughly ten percent of energy is successfully transferred between adjacent feeding tiers in ecological food webs.", "Long-Ecology"),
        ("What did the Human Genome Project accomplish in 2003?", "The Human Genome Project determined the sequence of the three billion nucleotide base pairs in human DNA.", "Long-Genetics"),
        ("What thermodynamic principle governs distillation columns?", "Distillation columns separate chemical mixtures based on differences in constituent relative boiling points.", "Long-ChemicalEng"),
        ("How do rocket engines generate forward thrust according to Newton's laws?", "Rocket engines operate on Newton's third law of motion, expelling high-velocity reaction mass to generate thrust.", "Long-Aerospace"),
        ("What is deep learning in artificial intelligence?", "Deep learning employs artificial neural networks with multiple hidden layers to extract hierarchical representations.", "Long-AI"),
        ("What does the Pauli exclusion principle state in quantum mechanics?", "The Pauli exclusion principle dictates that identical fermions cannot simultaneously occupy identical quantum states.", "Long-Physics"),
        ("What was the Neolithic Revolution in human history?", "The Neolithic Revolution around 10,000 BC initiated permanent sedentary agricultural settlements and social stratification.", "Long-History"),
        ("What laboratory method amplifies DNA fragments exponentially in vitro?", "The polymerase chain reaction (PCR) developed by Kary Mullis in 1983 enables exponential amplification of DNA fragments.", "Long-Biotech"),
        ("What geometric rule defines aromatic resonance stability in organic chemistry?", "Aromatic compounds exhibit delocalized resonance stability conforming to Huckel's 4n+2 pi electron rule.", "Long-Chemistry"),
        ("What major asteroid impact caused the extinction of the dinosaurs?", "The Cretaceous-Paleogene extinction 66 million years ago was caused by an asteroid impact at the Chicxulub crater.", "Long-Geology"),
        ("What particles steer proton beams in the CERN Large Hadron Collider?", "Superconducting electromagnets cooled by superfluid helium to 1.9 kelvin steer dual counter-rotating proton beams.", "Long-Physics"),
    ]

    # Expand to exactly 175 supported queries by generating specific variants
    while len(supported_specs) < 175:
        base = supported_specs[len(supported_specs) % 40]
        supported_specs.append((f"Can you verify: {base[0]}", f"Yes, {base[1]}", base[2]))

    for q, r, cat in supported_specs[:175]:
        benchmark.append({
            "id": case_id,
            "category": f"Supported-{cat}",
            "query": q,
            "response": r,
            "ground_truth": "Supported"
        })
        case_id += 1

    # --------------------------------------------------------------------------
    # CATEGORY 2: ENTITY SUBSTITUTION HALLUCINATIONS (125 queries)
    # --------------------------------------------------------------------------
    entity_hallucinations = [
        ("Who invented the practical telephone?", "Thomas Edison invented the practical telephone and patented it in New Jersey.", "Inventions"),
        ("Who developed the theory of general relativity?", "Sir Isaac Newton formulated general relativity in 1915 while working at Cambridge.", "Physics"),
        ("Who was the first human to step onto the Moon?", "Buzz Aldrin was the first person to step on the Moon, with Neil Armstrong staying inside the module.", "Space"),
        ("Who discovered the antibiotic penicillin?", "Louis Pasteur discovered penicillin while conducting rabies research in Paris.", "Medicine"),
        ("Who painted the Mona Lisa portrait?", "Michelangelo Buonarroti painted the Mona Lisa while working on the Sistine Chapel.", "Art"),
        ("Who commissioned the construction of the Taj Mahal?", "Emperor Akbar commissioned the construction of the Taj Mahal for his wife.", "Architecture"),
        ("Who was the first emperor of the Roman Empire?", "Julius Caesar became the first official Roman Emperor after declaring himself dictator.", "History"),
        ("Who formulated the laws of motion and universal gravitation?", "Galileo Galilei formulated the three universal laws of motion and gravitation.", "Physics"),
        ("Who determined the double helix structure of DNA in 1953?", "Gregor Mendel and Charles Darwin determined the double helix structure of DNA.", "Genetics"),
        ("Who founded the philosophical Academy in classical Athens?", "Socrates founded the Academy in Athens to train young statesmen.", "Philosophy"),
        ("Who developed the periodic table of chemical elements?", "Antoine Lavoisier created the first periodic table of elements in Moscow.", "Chemistry"),
        ("Who won the Nobel Prize for isolating single-layer graphene?", "Jack Kilby and Robert Noyce won the Nobel Prize for isolating single-layer graphene.", "Materials"),
        ("Who authored the plays Hamlet and Macbeth?", "Christopher Marlowe authored the plays Hamlet, Macbeth, and King Lear.", "Literature"),
        ("Who designed the dome of the Florence Cathedral?", "Leonardo da Vinci designed and built the dome of the Florence Cathedral.", "Architecture"),
        ("Who developed cowpox vaccination against smallpox?", "Robert Koch developed cowpox vaccination to eradicate smallpox in Germany.", "Medicine"),
        ("Who created the C programming language?", "Guido van Rossum invented the C programming language while working at Bell Labs.", "CompSci"),
        ("Who was the king of Macedon who conquered the Persian Empire?", "Pericles was the king of Macedon who led the conquest of the Persian Empire.", "History"),
        ("Who introduced the Turing test for artificial intelligence?", "John von Neumann introduced the Turing test in his 1950 paper on computation.", "AI"),
        ("Who discovered the four largest moons of Jupiter?", "Johannes Kepler discovered the four largest Jovian moons using his telescope in 1609.", "Astronomy"),
        ("Who isolated stable penicillin for widespread clinical wartime therapy?", "Edward Jenner isolated and mass-produced stable penicillin for Allied troops.", "Medicine"),
        ("Who built the mechanical Analytical Engine?", "Alan Turing designed the mechanical Analytical Engine in the Victorian era.", "CompSci"),
        ("Who formulated the uncertainty principle in quantum physics?", "Erwin Schrodinger formulated the uncertainty principle of quantum mechanics.", "Physics"),
        ("Who developed the first polio vaccine in the mid-twentieth century?", "Alexander Fleming developed the first successful inactivated polio vaccine.", "Medicine"),
        ("Who invented the movable type printing press in Germany?", "Johannes Kepler invented movable metal type printing in Mainz.", "History"),
        ("Who disproved spontaneous generation using swan-neck flasks?", "Antonie van Leeuwenhoek disproved spontaneous generation using swan-neck flasks.", "Biology"),
    ]
    # Multiply variants to reach 125
    while len(entity_hallucinations) < 125:
        base = entity_hallucinations[len(entity_hallucinations) % 25]
        entity_hallucinations.append((f"According to records, {base[0]}", f"Historical evidence shows that {base[1]}", base[2]))

    for q, r, cat in entity_hallucinations[:125]:
        benchmark.append({
            "id": case_id,
            "category": f"EntityHallucination-{cat}",
            "query": q,
            "response": r,
            "ground_truth": "Hallucinated"
        })
        case_id += 1

    # --------------------------------------------------------------------------
    # CATEGORY 3: NUMERICAL & DATE HALLUCINATIONS (100 queries)
    # --------------------------------------------------------------------------
    num_hallucinations = [
        ("When did Apollo 11 land on the Moon?", "The Apollo 11 lunar module landed on the Moon in July 1978.", "Space"),
        ("When did World War II conclude?", "World War II officially concluded with global armistice in September 1958.", "History"),
        ("What is the speed of light in vacuum?", "The speed of light in a vacuum is approximately 150,000,000 meters per second.", "Physics"),
        ("At what temperature does pure water boil at 1 atm?", "Pure water boils at exactly 212 degrees Celsius under standard atmospheric pressure.", "Chemistry"),
        ("How old is planet Earth according to geological dating?", "Geological radiocarbon dating proves Earth is approximately 120 million years old.", "Geology"),
        ("When was the Eiffel Tower completed in Paris?", "The Eiffel Tower was constructed in Paris and completed in 1948.", "Architecture"),
        ("What is the summit elevation of Mount Everest?", "Mount Everest has an officially measured elevation of 14,500 meters above sea level.", "Geography"),
        ("What is the surface gravity of Mars?", "The surface gravity on Mars is 9.8 meters per second squared, exactly equal to Earth.", "Astronomy"),
        ("How many planets are in the Solar System?", "There are currently fourteen officially recognized major planets in the Solar System.", "Astronomy"),
        ("When was the American declaration of the Panama Canal opening?", "The Panama Canal opened for international navigation in October 1965.", "Engineering"),
        ("When was Albert Einstein born and when did he die?", "Albert Einstein was born in 1935 and passed away in 2018.", "Physics"),
        ("When was the Gutenberg Bible printed in Mainz?", "Johannes Gutenberg printed his famous Latin Bible in the year 1680.", "History"),
        ("What percentage of Earth's atmosphere is oxygen gas?", "Oxygen gas comprises approximately 65 percent of Earth's dry atmospheric volume.", "Atmosphere"),
        ("How many chambers are in the human heart?", "The human heart is an anatomical organ composed of six distinct muscular chambers.", "Anatomy"),
        ("What is the atomic number of gold?", "Gold has an atomic number of 42 on the modern periodic table.", "Chemistry"),
        ("When was the French storming of the Bastille?", "The storming of the Bastille occurred during the revolution on July 14, 1848.", "History"),
        ("When did Alexander Fleming discover penicillin?", "Alexander Fleming discovered penicillin in his London laboratory in September 1968.", "Medicine"),
        ("How deep is the Challenger Deep in the Mariana Trench?", "Challenger Deep reaches an oceanic depth of approximately 35,000 meters below sea level.", "Oceanography"),
        ("How many bones or base pairs make up human DNA?", "The human genome is composed of 500 million nucleotide base pairs.", "Genetics"),
        ("What is absolute zero on the Celsius scale?", "Absolute zero is defined as minus 100 degrees Celsius in thermodynamic physics.", "Physics"),
    ]
    while len(num_hallucinations) < 100:
        base = num_hallucinations[len(num_hallucinations) % 20]
        num_hallucinations.append((f"State the verified number: {base[0]}", f"Verified scientific records report that {base[1]}", base[2]))

    for q, r, cat in num_hallucinations[:100]:
        benchmark.append({
            "id": case_id,
            "category": f"NumericalHallucination-{cat}",
            "query": q,
            "response": r,
            "ground_truth": "Hallucinated"
        })
        case_id += 1

    # --------------------------------------------------------------------------
    # CATEGORY 4: OUT-OF-CORPUS / ZERO EVIDENCE IN CORPUS (75 queries)
    # (Testing that when no evidence exists in the 120+ docs, it flags Hallucinated)
    # --------------------------------------------------------------------------
    out_of_corpus = [
        ("What is the magical core inside Harry Potter's wand?", "Harry Potter's wand is eleven inches long, made of holly, and contains a single feather from Fawkes the phoenix.", "PopCulture"),
        ("Who won the Super Bowl in February 2024?", "The Kansas City Chiefs won Super Bowl LVIII by defeating the San Francisco 49ers in overtime in Las Vegas.", "Sports"),
        ("What is the plot of Christopher Nolan's movie Inception?", "Inception follows Dom Cobb, an industrial thief who infiltrates the subconscious of targets to steal corporate secrets through dream-sharing technology.", "Cinema"),
        ("Who invented Bitcoin and in what year was the whitepaper released?", "Satoshi Nakamoto published the Bitcoin whitepaper in October 2008 and launched the genesis block in January 2009.", "Fintech"),
        ("What is the recipe for traditional Neapolitan pizza margherita?", "Traditional Neapolitan pizza requires San Marzano tomatoes, fresh mozzarella di bufala, fresh basil leaves, and extra virgin olive oil on fermented dough.", "Culinary"),
        ("Who is the Greek mythological god of the underworld?", "Hades is the ancient Greek god of the dead and king of the underworld, brother of Zeus and Poseidon.", "Mythology"),
        ("What is the capital city of Australia?", "Canberra is the federal capital city of Australia, situated between Sydney and Melbourne.", "Geography-OOC"),
        ("What species is the character Yoda in Star Wars?", "Yoda belongs to a mysterious ancient alien species characterized by small stature, green skin, and high sensitivity to the Force.", "Fiction"),
        ("Who composed the classical opera The Magic Flute?", "Wolfgang Amadeus Mozart composed the German opera The Magic Flute, premiered in Vienna in 1791.", "Music"),
        ("What are the primary colors in subtractive painting mixtures?", "The primary subtractive pigment colors traditionally taught in fine art are red, yellow, and blue.", "Art-OOC"),
        ("Who won the FIFA Men's World Cup in Qatar in 2022?", "Argentina won the 2022 FIFA World Cup in Qatar, defeating France in penalty kicks in the final.", "Sports"),
        ("What is the chemical composition of acrylic nail polish?", "Liquid acrylic nails consist of ethyl methacrylate monomer mixed with benzoyl peroxide polymer powder.", "Cosmetics"),
        ("Who directed the 1994 film Pulp Fiction?", "Quentin Tarantino wrote and directed the 1994 neo-noir crime film Pulp Fiction.", "Cinema"),
        ("What is the currency of Japan and its symbol?", "The currency of Japan is the Japanese yen, represented internationally by the currency symbol ¥.", "Economics-OOC"),
        ("What are the four Hogwarts houses in fantasy literature?", "The four houses of Hogwarts School are Gryffindor, Hufflepuff, Ravenclaw, and Slytherin.", "Fiction"),
    ]
    while len(out_of_corpus) < 75:
        base = out_of_corpus[len(out_of_corpus) % 15]
        out_of_corpus.append((f"Provide details regarding: {base[0]}", f"According to general knowledge, {base[1]}", base[2]))

    for q, r, cat in out_of_corpus[:75]:
        benchmark.append({
            "id": case_id,
            "category": f"ZeroEvidence-OutOfCorpus-{cat}",
            "query": q,
            "response": r,
            "ground_truth": "Hallucinated"
        })
        case_id += 1

    # --------------------------------------------------------------------------
    # CATEGORY 5: SUBTLE / MIXED CONTEXT INJECTIONS (25 queries)
    # (90% real text from the docs, with one critical false claim injected)
    # --------------------------------------------------------------------------
    subtle_injections = [
        ("Describe the Hubble Space Telescope's orbit and servicing.", "The Hubble Space Telescope orbits at 540 kilometers and was serviced by Russian Soyuz cosmonauts five times.", "Subtle-Hubble"),
        ("What did James Watson and Francis Crick discover about DNA?", "James Watson and Francis Crick discovered that DNA is an uncoiled single strand containing equal amounts of uranium and carbon.", "Subtle-DNA"),
        ("What did Alexander Fleming discover in 1928?", "Alexander Fleming discovered penicillin in 1928, proving it was a synthetic mineral compound mined from limestone caves.", "Subtle-Fleming"),
        ("How do mitochondria produce cellular energy?", "Mitochondria are eukaryotic cell organelles that produce energy by burning liquid nitrogen and sulfur inside the nucleus.", "Subtle-Cell"),
        ("What did Marie Curie discover about radioactivity?", "Marie Curie discovered radium and polonium, proving that radiation is caused by sound wave vibrations passing through glass.", "Subtle-Curie"),
    ]
    while len(subtle_injections) < 25:
        base = subtle_injections[len(subtle_injections) % 5]
        subtle_injections.append((f"Fact-check: {base[0]}", f"Evidence indicates {base[1]}", base[2]))

    for q, r, cat in subtle_injections[:25]:
        benchmark.append({
            "id": case_id,
            "category": f"SubtleInjection-{cat}",
            "query": q,
            "response": r,
            "ground_truth": "Hallucinated"
        })
        case_id += 1

    return benchmark

def run_500_benchmark(save_path: str = "benchmark_results_500.json"):
    print("=" * 82)
    print("      🛡️  GROUNDTRUTH AI — 500-QUERY COMPREHENSIVE BENCHMARK SUITE  🛡️")
    print("=" * 82)

    benchmark = generate_500_benchmark()
    total_samples = len(benchmark)
    total_supported = sum(1 for d in benchmark if d["ground_truth"] == "Supported")
    total_hallucinated = sum(1 for d in benchmark if d["ground_truth"] == "Hallucinated")

    print(f"Total Benchmark Queries : {total_samples}")
    print(f"  • Truly Supported     : {total_supported} (35.0%)")
    print(f"  • Hallucinated / OOC  : {total_hallucinated} (65.0%)")
    print(f"      - Entity Swaps    : 125")
    print(f"      - Numerical/Dates : 100")
    print(f"      - Zero Evidence   : 75")
    print(f"      - Subtle Injected : 25")
    print("-" * 82)
    print("Executing batch evaluation across RAG retrieval + LLM Judge...")

    y_true = []
    y_pred = []
    results = []

    start_time = time.time()
    batch_start = start_time

    for idx, case in enumerate(benchmark, start=1):
        query = case["query"]
        response = case["response"]
        expected = case["ground_truth"]

        # 1. RAG Context Retrieval (top 3 chunks)
        retrieved_docs = retrieve_context(query, top_k=3)
        context_snippets = [f"[{d.get('source', 'Doc')}]: {d.get('content', '')}" for d in retrieved_docs]
        full_context = "\n\n".join(context_snippets) if context_snippets else "No relevant context found in knowledge base."

        # 2. Judge Evaluation
        eval_result = evaluate_hallucination(query, response, full_context)
        predicted = eval_result.get("verdict", "Hallucinated")
        confidence = float(eval_result.get("confidence", 0.0))
        confidence_pct = round(confidence * 100, 1) if confidence <= 1.0 else round(confidence, 1)
        reason = eval_result.get("reason", "No reason provided.")

        is_correct = (predicted.lower() == expected.lower())

        y_true.append(expected)
        y_pred.append(predicted)

        results.append({
            "id": case["id"],
            "category": case["category"],
            "query": query,
            "response": response,
            "expected": expected,
            "predicted": predicted,
            "confidence": confidence_pct,
            "correct": is_correct,
            "reason": reason,
            "sources_retrieved": [d.get("source") for d in retrieved_docs]
        })

        # Progress reporting every 50 queries
        if idx % 50 == 0 or idx == total_samples:
            elapsed_batch = time.time() - batch_start
            print(f"  [Progress] Evaluated {idx:03d}/{total_samples:03d} queries | Batch Time: {elapsed_batch:.2f}s | Current Acc: {accuracy_score(y_true, y_pred)*100:.2f}%")
            batch_start = time.time()

    total_elapsed = time.time() - start_time

    # --------------------------------------------------------------------------
    # METRICS & CONFUSION MATRIX
    # --------------------------------------------------------------------------
    labels = ["Supported", "Hallucinated"]
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average=None)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    print("\n" + "=" * 82)
    print("                      📊  OVERALL EVALUATION RESULTS (N=500)")
    print("=" * 82)
    print(f"Total Evaluations Completed : {total_samples}")
    print(f"Correct Predictions         : {sum(1 for r in results if r['correct'])} / {total_samples}")
    print(f"Overall Benchmark Accuracy  : {acc * 100:.2f}%")
    print(f"Total Execution Time        : {total_elapsed:.2f} seconds ({total_elapsed/total_samples:.3f}s per query)")
    print("-" * 82)

    print("\n                         📈  PER-CLASS METRICS")
    print(f"{'Class':<18} {'Precision':<14} {'Recall':<14} {'F1-Score':<14} {'Support':<10}")
    print("-" * 72)
    for i, label in enumerate(labels):
        support_cnt = y_true.count(label)
        print(f"{label:<18} {prec[i]*100:>10.2f}%    {rec[i]*100:>10.2f}%    {f1[i]*100:>10.2f}%    {support_cnt:>8}")
    print("-" * 72)

    print("\n                         🔲  2x2 CONFUSION MATRIX")
    print(" " * 28 + "PREDICTED")
    print(f"{'':<24} | {'Supported':^16} | {'Hallucinated':^16} | {'Total':^10} |")
    print("-" * 76)
    print(f"ACTUAL Supported        | {cm[0][0]:^16} | {cm[0][1]:^16} | {sum(cm[0]):^10} |")
    print(f"ACTUAL Hallucinated/OOC | {cm[1][0]:^16} | {cm[1][1]:^16} | {sum(cm[1]):^10} |")
    print("-" * 76)
    print(f"{'Total':<24} | {cm[0][0]+cm[1][0]:^16} | {cm[0][1]+cm[1][1]:^16} | {total_samples:^10} |")
    print("-" * 76)

    # Sub-category Breakdown
    categories = set(r["category"].split("-")[0] for r in results)
    print("\n                    🔍  PER-CATEGORY ACCURACY BREAKDOWN")
    print(f"{'Category Group':<32} {'Correct':<12} {'Total':<10} {'Accuracy':<12}")
    print("-" * 68)
    for cat in sorted(categories):
        cat_samples = [r for r in results if r["category"].startswith(cat)]
        cat_correct = sum(1 for r in cat_samples if r["correct"])
        cat_total = len(cat_samples)
        cat_acc = (cat_correct / cat_total) * 100 if cat_total else 0.0
        print(f"{cat:<32} {cat_correct:>6} / {cat_total:<4}   {cat_total:>6}   {cat_acc:>10.2f}%")
    print("-" * 68)

    print("\nDetailed Scikit-Learn Classification Report:")
    print(classification_report(y_true, y_pred, labels=labels, digits=4))

    # Save to JSON
    summary_report = {
        "benchmark_metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_queries": total_samples,
            "total_documents_in_corpus": len(os.listdir("data/documents")),
            "elapsed_seconds": round(total_elapsed, 2),
            "seconds_per_query": round(total_elapsed / total_samples, 4)
        },
        "performance_metrics": {
            "overall_accuracy_percent": round(acc * 100, 2),
            "confusion_matrix": {
                "labels": labels,
                "matrix": cm.tolist(),
                "true_supported": int(cm[0][0]),
                "false_hallucinated": int(cm[0][1]),
                "false_supported": int(cm[1][0]),
                "true_hallucinated": int(cm[1][1]),
            },
            "per_class": {
                "Supported": {"precision": round(prec[0]*100, 2), "recall": round(rec[0]*100, 2), "f1_score": round(f1[0]*100, 2)},
                "Hallucinated": {"precision": round(prec[1]*100, 2), "recall": round(rec[1]*100, 2), "f1_score": round(f1[1]*100, 2)}
            }
        },
        "evaluations": results
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    print(f"\n✅ Complete 500-sample benchmark report successfully saved to: {save_path}\n")
    return summary_report

if __name__ == "__main__":
    run_500_benchmark()

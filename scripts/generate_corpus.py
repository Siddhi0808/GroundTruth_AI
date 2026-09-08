import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DOC_DIR = Path("data/documents")
DOC_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
title_style = styles["Heading1"]
normal_style = styles["Normal"]

def make_pdf(filename: str, title: str, paragraphs: list[str]):
    filepath = DOC_DIR / filename
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story = [Paragraph(title, title_style), Spacer(1, 14)]
    for p in paragraphs:
        story.append(Paragraph(p, normal_style))
        story.append(Spacer(1, 8))
    doc.build(story)
    print(f"Created PDF: {filename} ({len(paragraphs)} paragraphs)")

def make_txt(filename: str, lines: list[str]):
    filepath = DOC_DIR / filename
    content = "\n".join(lines).strip() + "\n"
    filepath.write_text(content, encoding="utf-8")
    print(f"Created TXT: {filename} ({len(lines)} lines)")

# ==============================================================================
# 1. MICRO DOCUMENTS (Strictly 2 lines each)
# ==============================================================================
micro_docs = [
    ("micro_speed_of_light.txt", [
        "The speed of light in a vacuum is exactly 299,792,458 meters per second.",
        "It is symbolized by the letter c in physical equations including E equals mc squared."
    ]),
    ("micro_water_boiling.txt", [
        "Pure liquid water boils at exactly 100 degrees Celsius at standard atmospheric pressure.",
        "Its freezing point under standard conditions occurs at zero degrees Celsius."
    ]),
    ("micro_mars_gravity.txt", [
        "The surface gravity of Mars is approximately 3.72 meters per second squared.",
        "This is roughly 38 percent of the surface gravity experienced on Earth."
    ]),
    ("micro_dna_bases.txt", [
        "Deoxyribonucleic acid is composed of four nucleotide chemical bases: adenine, thymine, cytosine, and guanine.",
        "In double-stranded DNA, adenine always pairs with thymine and cytosine pairs with guanine."
    ]),
    ("micro_jupiter_great_red_spot.txt", [
        "The Great Red Spot is a persistent high-pressure storm located on Jupiter's southern hemisphere.",
        "It has been observed continuously by astronomers for more than three centuries."
    ]),
    ("micro_penicillin_discovery.txt", [
        "Alexander Fleming discovered penicillin at St Mary's Hospital in London in September 1928.",
        "It was the first widely used natural antibiotic produced by the Penicillium notatum mould."
    ]),
    ("micro_gold_atomic_number.txt", [
        "Gold is a chemical transition metal with the atomic symbol Au and atomic number 79.",
        "It is one of the least reactive chemical elements and is completely solid under standard conditions."
    ]),
    ("micro_mount_everest.txt", [
        "Mount Everest has an official summit elevation of 8,848.86 meters above sea level.",
        "It is located in the Mahalangur Himal sub-range of the Himalayas on the border of Nepal and China."
    ]),
    ("micro_pacific_ocean.txt", [
        "The Pacific Ocean is the largest and deepest ocean basin on Earth, covering over 165 million square kilometers.",
        "It contains the Mariana Trench, the deepest oceanic trench on the planet."
    ]),
    ("micro_mitochondria.txt", [
        "Mitochondria are membrane-bound organelles found in the cytoplasm of eukaryotic cells.",
        "They generate most of the chemical energy needed by the cell in the form of adenosine triphosphate."
    ]),
    ("micro_oxygen_content.txt", [
        "Oxygen gas accounts for approximately 20.95 percent of Earth's modern dry atmosphere by volume.",
        "Nitrogen is the most abundant atmospheric gas, comprising approximately 78.08 percent."
    ]),
    ("micro_turing_machine.txt", [
        "Alan Turing introduced the concept of the Turing machine in his seminal 1936 mathematical paper.",
        "It serves as the foundational theoretical model for modern general-purpose digital computation."
    ]),
    ("micro_sahara_desert.txt", [
        "The Sahara is the largest hot desert in the world, spanning an area of approximately 9.2 million square kilometers.",
        "It covers much of North Africa across eleven sovereign nations."
    ]),
    ("micro_table_salt.txt", [
        "Common table salt is an ionic chemical compound known systematically as sodium chloride.",
        "Its chemical formula is NaCl, containing equal molar proportions of sodium and chlorine."
    ]),
    ("micro_photosynthesis.txt", [
        "Photosynthesis is the biochemical process used by green plants to convert solar light energy into glucose.",
        "The process consumes carbon dioxide and water while producing molecular oxygen as a byproduct."
    ]),
    ("micro_helium_element.txt", [
        "Helium is a colorless, odorless, and inert noble gas with the atomic number 2.",
        "It is the second-lightest and second-most abundant element in the observable universe."
    ]),
    ("micro_venus_rotation.txt", [
        "Venus rotates in the opposite direction to most other solar system planets, known as retrograde rotation.",
        "A single sidereal day on Venus lasts approximately 243 Earth solar days."
    ]),
    ("micro_great_wall_china.txt", [
        "The Great Wall of China was constructed along the historical northern borders of ancient Chinese states.",
        "The most comprehensive and preserved remaining sections were built during the Ming dynasty."
    ]),
    ("micro_diamond_hardness.txt", [
        "Diamond is an allotrope of pure carbon with atoms arranged in a tetrahedral crystal lattice.",
        "It rates a maximum 10 on the Mohs scale of mineral hardness, making it exceptionally scratch-resistant."
    ]),
    ("micro_gravity_constant.txt", [
        "The universal Newtonian gravitational constant G has an approximate value of 6.674 times 10 to the negative 11th.",
        "It defines the proportional strength of the gravitational force between masses in universal physics."
    ]),
    ("micro_pluto_classification.txt", [
        "The International Astronomical Union reclassified Pluto from a major planet to a dwarf planet in August 2006.",
        "Pluto resides in the Kuiper belt, a circumstellar disc of icy celestial bodies beyond Neptune."
    ]),
    ("micro_amazon_river.txt", [
        "The Amazon River in South America is the largest river in the world by water discharge volume.",
        "It flows primarily through Peru, Colombia, and Brazil before emptying into the Atlantic Ocean."
    ]),
    ("micro_steam_engine_watt.txt", [
        "James Watt patented his separate condenser improvement for steam engines in 1769.",
        "This modification radically improved mechanical fuel efficiency and drove the Industrial Revolution."
    ]),
    ("micro_absolute_zero.txt", [
        "Absolute zero is the lowest possible theoretical temperature, defined as zero kelvin or minus 273.15 Celsius.",
        "At absolute zero, thermodynamic system entropy reaches its minimum value and particle motion ceases."
    ]),
    ("micro_saturn_rings.txt", [
        "Saturn possesses the most extensive and visible planetary ring system in the Solar System.",
        "The rings are composed predominantly of billions of water ice particles and minor rocky dust."
    ])
]

for fname, lines in micro_docs:
    make_txt(fname, lines)

# ==============================================================================
# 2. MEDIUM DOCUMENTS (10 to 30 lines) - Both TXT and PDF
# ==============================================================================
medium_txt_data = [
    ("hubble_space_telescope.txt", [
        "The Hubble Space Telescope is a large optical space observatory deployed into low Earth orbit in April 1990.",
        "It was carried into space aboard Space Shuttle Discovery during mission STS-31.",
        "Hubble orbits at an approximate altitude of 540 kilometers above Earth's surface.",
        "Operating above the distortion of Earth's atmosphere allows Hubble to capture exceptionally sharp astronomical imagery.",
        "It has made more than 1.5 million astronomical observations during its decades of operation.",
        "Key scientific contributions include determining the expansion rate of the universe, known as the Hubble constant.",
        "Hubble also provided decisive proof that supermassive black holes reside at the center of most major galaxies.",
        "The observatory was serviced five separate times by astronaut crews flying on the Space Shuttle.",
        "Servicing missions replaced degraded gyroscopes, upgraded scientific cameras, and corrected optical aberrations.",
        "Hubble continues to collaborate alongside the newer James Webb Space Telescope across complementary electromagnetic wavelengths."
    ]),
    ("voyager_missions.txt", [
        "The Voyager program consists of two robotic space probes, Voyager 1 and Voyager 2, launched by NASA in 1977.",
        "Their primary mission was to explore the giant outer planets of our Solar System: Jupiter and Saturn.",
        "Voyager 2 continued past Saturn to execute the only flybys of the ice giants Uranus in 1986 and Neptune in 1989.",
        "Both probes are powered by radioisotope thermoelectric generators utilizing plutonium-238.",
        "In August 2012, Voyager 1 became the first human-made spacecraft to cross the heliopause into interstellar space.",
        "Voyager 2 crossed the heliopause into interstellar space several years later in November 2018.",
        "Each spacecraft carries a gold-plated copper phonograph record containing sounds and images selected to portray Earth.",
        "The Golden Records include musical compositions, spoken greetings in fifty-five human languages, and natural ambient sounds.",
        "Instruments on both probes continue measuring magnetic fields, cosmic rays, and plasma density in deep space.",
        "NASA expects communications to gradually diminish as electrical generator power drops below operational thresholds."
    ]),
    ("james_webb_telescope.txt", [
        "The James Webb Space Telescope, commonly abbreviated JWST, is a space telescope specialized in infrared astronomy.",
        "It was launched on December 25, 2021, aboard an Ariane 5 rocket from the European Spaceport in Kourou, French Guiana.",
        "JWST operates in a halo orbit around the Sun-Earth second Lagrange point, L2, roughly 1.5 million kilometers from Earth.",
        "Its primary mirror consists of eighteen hexagonal gold-coated beryllium mirror segments spanning 6.5 meters in total diameter.",
        "This mirror provides more than six times the light-collecting surface area of the Hubble Space Telescope.",
        "JWST is equipped with a five-layer Kapton sunshield that keeps its scientific instruments below fifty kelvin.",
        "The telescope's core instruments include the Near-Infrared Camera, Near-Infrared Spectrograph, and Mid-Infrared Instrument.",
        "JWST is designed to study the earliest stars and galaxies that formed following the Big Bang.",
        "It also characterizes exoplanet atmospheres, searching for chemical signatures of water, methane, and carbon dioxide.",
        "Initial deep-field imagery revealed unprecedented details of gravitational lensing and distant cosmic structures."
    ]),
    ("black_holes.txt", [
        "A black hole is a region of spacetime where gravitational acceleration is so intense that nothing can escape from it.",
        "Not even electromagnetic radiation such as light has sufficient velocity to overcome the gravitational pull.",
        "The boundary of a black hole from which escape is impossible is called the event horizon.",
        "At the center of a non-rotating black hole lies a gravitational singularity where spacetime curvature becomes infinite.",
        "Stellar-mass black holes typically form when massive stars collapse at the end of their thermonuclear lifecycles.",
        "Supermassive black holes containing millions to billions of solar masses reside in the nuclei of almost all galaxies.",
        "The supermassive black hole at the center of our Milky Way galaxy is known as Sagittarius A-star.",
        "In 2019, the Event Horizon Telescope collaboration released the first direct visual image of the shadow of a black hole.",
        "That image depicted the supermassive black hole situated at the center of the giant elliptical galaxy Messier 87.",
        "Physicist Stephen Hawking demonstrated theoretically that black holes should emit thermal radiation known as Hawking radiation."
    ]),
    ("crispr_gene_editing.txt", [
        "CRISPR-Cas9 is an RNA-guided gene-editing technology adapted from a natural bacterial defense mechanism against viruses.",
        "Bacteria capture snippets of viral DNA and use them to construct CRISPR arrays that remember past viral invaders.",
        "The Cas9 enzyme acts as molecular scissors capable of cutting double-stranded DNA at exact designated target sites.",
        "Scientists design synthetic guide RNA molecules that navigate the Cas9 endonuclease to matching genomic sequences.",
        "Once Cas9 introduces a double-strand break, cellular repair pathways repair the cut, allowing gene modification or insertion.",
        "Jennifer Doudna and Emmanuelle Charpentier were awarded the 2020 Nobel Prize in Chemistry for developing this technology.",
        "CRISPR enables targeted therapeutic interventions for genetic disorders including sickle cell anemia and beta thalassemia.",
        "In agriculture, researchers utilize CRISPR to engineer crops with superior drought resistance and improved nutritional yields.",
        "Ethical considerations have emerged regarding the genetic modification of human reproductive germline cells.",
        "Continuous refinements such as base editing and prime editing seek to minimize unintentional off-target genomic cleavage."
    ]),
    ("marie_curie.txt", [
        "Marie Curie was a Polish-born French physicist and chemist who conducted pioneering research on radioactivity.",
        "She was the first woman to win a Nobel Prize and remains the only person to win Nobel Prizes in two distinct scientific fields.",
        "In 1903, she shared the Nobel Prize in Physics with Pierre Curie and Henri Becquerel for their investigations into radiation.",
        "In 1911, Marie Curie won the Nobel Prize in Chemistry for discovering the radioactive elements radium and polonium.",
        "She named polonium after her native homeland of Poland, which was then divided under foreign partition.",
        "Curie coined the word radioactivity to describe the spontaneous emission of penetrating rays by unstable atomic nuclei.",
        "During World War I, she established and directed mobile radiography vehicles to assist battlefield military surgeons.",
        "She founded the Radium Institute in Paris, which became a premier international center for nuclear physics and oncology.",
        "Her persistent occupational exposure to high levels of ionizing radiation caused her to develop aplastic anemia.",
        "Her historical scientific notebooks and laboratory apparatus remain highly radioactive and must be stored in lead-lined containers."
    ]),
    ("plate_tectonics.txt", [
        "Plate tectonics is the foundational scientific theory explaining the large-scale motion of seven major Earth lithospheric plates.",
        "The rigid outer mechanical layer of the Earth, the lithosphere, is fractured into continually moving tectonic plates.",
        "These lithospheric plates glide atop the ductile, semi-fluid asthenosphere beneath them through convective mantle currents.",
        "Tectonic boundaries are classified into divergent, convergent, and transform boundaries based on relative plate motion.",
        "At divergent boundaries, such as the Mid-Atlantic Ridge, oceanic crust spreads apart and new volcanic seafloor forms.",
        "At convergent boundaries, one plate subducts beneath another into the mantle, producing deep trenches and volcanic island arcs.",
        "The collision between the Indian and Eurasian continental plates produced the elevated Tibetan Plateau and Himalayas.",
        "Transform boundaries, exemplified by California's San Andreas Fault, involve horizontal sliding that triggers frequent earthquakes.",
        "Alfred Wegener first proposed the hypothesis of continental drift in 1912, citing geological and fossil correlations.",
        "Seafloor spreading discoveries and paleomagnetic reversal mapping during the 1960s confirmed the modern plate tectonic model."
    ]),
    ("charles_darwin.txt", [
        "Charles Darwin was an English naturalist, biologist, and geologist celebrated for developing the theory of biological evolution.",
        "He proposed that all species of life have descended over time from common ancestral lineages through natural selection.",
        "Darwin gathered extensive botanical, zoological, and geological specimens during his five-year voyage aboard HMS Beagle.",
        "His observations of mockingbirds and finches on the Galapagos Islands contributed significantly to his evolutionary insights.",
        "In 1859, Darwin published his foundational treatise titled On the Origin of Species by Means of Natural Selection.",
        "Natural selection posits that organisms possessing traits advantageous for survival are more likely to reproduce successfully.",
        "Over successive generations, beneficial adaptations accumulate within populations, driving the diversification of species.",
        "Darwin developed his ideas in close dialogue with naturalist Alfred Russel Wallace, who independently formulated natural selection.",
        "In subsequent works, including The Descent of Man, Darwin addressed sexual selection and human evolutionary origins.",
        "Darwin's evolutionary synthesis remains the unifying conceptual foundation of all contemporary biological sciences."
    ]),
    ("dna_double_helix.txt", [
        "The molecular structure of deoxyribonucleic acid was determined in 1953 by James Watson and Francis Crick.",
        "Their model relied on critical X-ray crystallography data collected by Rosalind Franklin and Raymond Gosling.",
        "Franklin's famous Photograph 51 provided crucial quantitative measurements demonstrating the helical architecture of DNA.",
        "DNA is organized as a right-handed double helix composed of two complementary anti-parallel polynucleotide strands.",
        "The outer structural backbone consists of alternating deoxyribose sugar rings and inorganic phosphate groups.",
        "The inner rungs consist of nitrogenous base pairs held together across the helical axis by hydrogen bonds.",
        "Adenine forms two hydrogen bonds exclusively with thymine, while guanine forms three hydrogen bonds with cytosine.",
        "This strict complementary base pairing provides a direct biological mechanism for exact genetic replication.",
        "Watson, Crick, and Maurice Wilkins received the 1962 Nobel Prize in Physiology or Medicine for their discoveries.",
        "Understanding the double helix structure revolutionized genetics, molecular diagnostics, biotechnology, and forensic medicine."
    ]),
    ("alexander_the_great.txt", [
        "Alexander the Great was king of the ancient Greek kingdom of Macedon from 336 BC until his death in 323 BC.",
        "He was tutored during his youth by the renowned philosopher Aristotle until age sixteen.",
        "Succeeding his father Philip II, Alexander launched military campaigns that conquered the vast Achaemenid Persian Empire.",
        "His empire extended from Greece and the Balkans across Egypt, the Levant, Mesopotamia, and into northwest India.",
        "Alexander remained undefeated in battle and is widely considered one of history's most successful military commanders.",
        "He established more than twenty cities bearing his name, the most famous being Alexandria in northern Egypt.",
        "His conquests initiated the Hellenistic period, during which Greek culture and language spread broadly across Afro-Eurasia.",
        "Alexander died in Babylon in 323 BC at the age of thirty-two without naming an unequivocal adult successor.",
        "His sudden death precipitated the Wars of the Diadochi, partitioning his immense empire among competing Macedonian generals.",
        "His tactical maneuvers and battlefield strategies continue to be studied in contemporary military academies."
    ]),
    ("french_revolution.txt", [
        "The French Revolution was a transformative period of social and political upheaval in France lasting from 1789 to 1799.",
        "It was sparked by severe financial deficits, widespread agricultural famine, and resentment of feudal aristocratic privileges.",
        "The storming of the Bastille fortress prison on July 14, 1789, became an enduring revolutionary symbol of popular rebellion.",
        "In August 1789, the National Constituent Assembly published the Declaration of the Rights of Man and of the Citizen.",
        "The monarchy was abolished in September 1792, and King Louis XVI was executed by guillotine in January 1793.",
        "The radical Reign of Terror, overseen by Maximilien Robespierre and the Committee of Public Safety, executed thousands.",
        "Robespierre was overthrown and executed in July 1794 during the Thermidorian Reaction, leading to the Directory.",
        "The Revolution replaced feudal structures with principles of secular equality, individual liberty, and popular sovereignty.",
        "It triggered significant military conflicts across Europe known collectively as the French Revolutionary Wars.",
        "The period concluded in November 1799 when General Napoleon Bonaparte seized state power in the Coup of 18 Brumaire."
    ]),
    ("industrial_revolution.txt", [
        "The Industrial Revolution marked the broad transition from agrarian and handicraft economies to machine-driven manufacturing.",
        "It originated in Great Britain during the mid-eighteenth century before spreading throughout Western Europe and North America.",
        "Key early mechanized innovations included John Kay's flying shuttle and James Hargreaves' spinning jenny.",
        "The perfection of the commercial steam engine by James Watt provided continuous mechanical power independent of flowing water.",
        "Abundant domestic coal deposits in Britain supplied the essential thermal fuel for metallurgical smelting and steam generation.",
        "Widespread railroad network construction revolutionized overland cargo transportation and drastically reduced freight transit times.",
        "Industrialization stimulated massive demographic migration from rural agrarian villages into burgeoning industrial cities.",
        "Early factory labor conditions were characterized by hazardous working environments, long shifts, and rampant child exploitation.",
        "These social strains stimulated the rise of organized labor trade unions and new socioeconomic theories including Marxism.",
        "The Industrial Revolution permanently expanded global productive output and fundamentally reshaped modern human society."
    ]),
    ("quantum_mechanics_intro.txt", [
        "Quantum mechanics is the fundamental physical theory describing nature at the atomic and subatomic scales.",
        "Classical Newtonian physics fails to predict observable phenomena when applied to microscopic atomic particles.",
        "Max Planck originated quantum theory in 1900 by proposing that electromagnetic energy is emitted in discrete units called quanta.",
        "Albert Einstein explained the photoelectric effect in 1905 by demonstrating that light behaves as discrete packets called photons.",
        "Niels Bohr introduced an atomic model where electrons occupy quantized orbital energy levels without continuously radiating.",
        "Louis de Broglie proposed wave-particle duality, suggesting all physical matter exhibits measurable wave characteristics.",
        "Werner Heisenberg formulated the uncertainty principle, demonstrating conjugate variables cannot both be known simultaneously.",
        "Erwin Schrodinger derived the fundamental wave equation calculating the probabilistic distribution of quantum states.",
        "Quantum phenomena underpin modern technologies including semiconductor microprocessors, laser communications, and atomic clocks.",
        "Contemporary research actively develops quantum computers designed to solve complex computational problems exponentially faster."
    ]),
    ("photosynthesis_overview.txt", [
        "Photosynthesis is the photochemical biological process whereby green plants, algae, and cyanobacteria synthesize carbohydrates.",
        "The primary light-absorbing pigment involved in photosynthetic energy capture is green chlorophyll.",
        "The overall chemical equation consumes six carbon dioxide molecules and six water molecules using photon energy.",
        "This reaction yields one glucose carbohydrate molecule and six molecules of molecular oxygen as a vital atmospheric byproduct.",
        "The process divides into light-dependent reactions within thylakoid membranes and light-independent reactions in the stroma.",
        "During light-dependent stages, absorbed sunlight splits water molecules via photolysis to release protons, electrons, and oxygen.",
        "Proton concentration gradients generate adenosine triphosphate and reduce NADP-plus into energetic NADPH.",
        "The light-independent Calvin cycle utilizes this stored chemical energy to fix atmospheric carbon dioxide into sugars.",
        "RuBisCO is the principal carboxylase enzyme catalyzing the initial fixation of carbon dioxide in the Calvin cycle.",
        "Virtually all planetary food chains and biological energy webs depend fundamentally upon photosynthetic solar conversion."
    ]),
    ("amazon_rainforest.txt", [
        "The Amazon rainforest is the world's most extensive moist tropical broadleaf biome, spanning the Amazon River basin.",
        "Covering roughly 5.5 million square kilometers, it represents over half of the planet's remaining tropical rainforest territory.",
        "The basin encompasses territory across nine South American nations, with approximately sixty percent situated within Brazil.",
        "The Amazon contains the greatest biodiversity of terrestrial flora and fauna found anywhere on the planet.",
        "It is home to an estimated 390 billion individual trees belonging to approximately 16,000 distinct species.",
        "The ecosystem functions as a critical planetary carbon sink, absorbing billions of tons of carbon dioxide from the atmosphere.",
        "Deforestation driven by cattle ranching, soybean cultivation, commercial logging, and road construction threatens its stability.",
        "Extensive deforestation disrupts regional hydrological cycles, reducing continental rainfall patterns and moisture recycling.",
        "Numerous indigenous nations have inhabited the Amazon basin for millennia, maintaining extensive ethnobotanical knowledge.",
        "International ecological initiatives prioritize conservation and sustainable stewardship to avoid ecological tipping points."
    ]),
    ("sahara_geography.txt", [
        "The Sahara is the largest sub-polar desert on Earth, encompassing over 9.2 million square kilometers across North Africa.",
        "It spans westward from the Atlantic Ocean eastward to the Red Sea, bordered southwards by the semi-arid Sahel transition belt.",
        "Landforms across the Sahara include vast wind-shaped sand dunes called ergs, barren gravel plains, and stony plateaus.",
        "Contrary to popular perceptions, sand dunes cover only approximately fifteen percent of the total desert terrain.",
        "The hyper-arid central regions experience annual precipitation averages below twenty-five millimeters.",
        "Daytime temperatures in summer frequently exceed fifty degrees Celsius, followed by rapid nocturnal radiational cooling.",
        "Thousands of years ago during the African Humid Period, the Sahara hosted lush grasslands, lakes, and abundant wildlife.",
        "Archaeological rock art across the Tassili n'Ajjer plateau depicts pastoral livestock herding and riverine animal life.",
        "Modern economic activities throughout the desert center on mineral extraction, phosphate mining, and hydrocarbon exploitation.",
        "Nomadic Tuareg and Bedouin communities maintain adapted cultural traditions traversing historical trans-Saharan caravan routes."
    ]),
    ("ancient_rome.txt", [
        "Ancient Rome began as an Italic settlement on the Italian peninsula during the eighth century BC along the Tiber River.",
        "According to foundational mythological tradition, the city of Rome was founded in 753 BC by twin brothers Romulus and Remus.",
        "Rome evolved from an early monarchy into the Roman Republic around 509 BC, governed by elected magistrates and the Senate.",
        "Through disciplined legionary warfare, the Republic expanded across Italy, Spain, Gaul, Greece, and North Africa.",
        "Civil wars and the rise of military commanders culminated in the collapse of the Republic and the emergence of the Empire.",
        "Octavian assumed the title Augustus in 27 BC, becoming the first Roman Emperor and inaugurating the Pax Romana.",
        "At its territorial zenith under Emperor Trajan in 117 AD, the Roman Empire encircled the entirety of the Mediterranean basin.",
        "Roman engineers excelled in infrastructure, constructing expansive paved roads, monumental aqueducts, and durable concrete arches.",
        "Roman legal principles, governance structures, Latin vocabulary, and architectural styles heavily shaped Western civilization.",
        "The Western Roman Empire disintegrated in 476 AD, while the Eastern Byzantine Empire endured in Constantinople until 1453."
    ]),
    ("ancient_egypt.txt", [
        "Ancient Egypt was a major civilization concentrated along the lower reaches of the Nile River in northeast Africa.",
        "Its historical consolidation occurred around 3100 BC with the political unification of Upper and Lower Egypt under King Menes.",
        "Civilization flourished primarily due to predictable seasonal Nile flooding that deposited fertile agricultural silt.",
        "The civilization is traditionally categorized into Old, Middle, and New Kingdom eras separated by intermediate crisis intervals.",
        "During the Old Kingdom Fourth Dynasty, monumental stone pyramids were constructed at Giza, including the Great Pyramid for Khufu.",
        "Egyptian society was ruled by divine monarchs termed pharaohs who administered complex administrative and priestly hierarchies.",
        "Religious beliefs emphasized the preservation of the physical body after death through mummification and the afterlife journey.",
        "Scribes recorded religious liturgies, royal decrees, and taxation accounts using formal hieroglyphic and cursive hieratic scripts.",
        "The 1799 discovery of the Rosetta Stone allowed Jean-Francois Champollion to decipher ancient Egyptian hieroglyphics in 1822.",
        "Pharaonic sovereignty ended in 30 BC when Roman forces defeated Queen Cleopatra VII, transforming Egypt into a Roman province."
    ]),
    ("renaissance_period.txt", [
        "The Renaissance was a fervent European cultural and intellectual movement marking the transition from the Middle Ages to modernity.",
        "It originated in fifteenth-century northern Italian city-states, most prominently Florence, funded by mercantile wealth.",
        "The intellectual philosophy of Renaissance humanism emphasized classical Greco-Roman scholarship, secular ethics, and rhetoric.",
        "Prominent patrons such as the Medici family commissioned monumental artworks and public architectural projects.",
        "Master polymaths including Leonardo da Vinci epitomized the Renaissance ideal through achievements in painting, anatomy, and engineering.",
        "Michelangelo Buonarroti sculpted the marble David and painted the ceiling frescoes of the Sistine Chapel in Rome.",
        "Johannes Gutenberg's development of movable type mechanical printing around 1440 exponentially accelerated book dissemination.",
        "Scientific developments gathered momentum, laying empirical foundations that culminated in the Scientific Revolution.",
        "Architect Filippo Brunelleschi designed and engineered the monumental self-supporting brick dome of the Florence Cathedral.",
        "The Renaissance profoundly reshaped European art, philosophical inquiry, literary genres, political theory, and educational systems."
    ]),
    ("printing_press.txt", [
        "The movable type printing press was developed in Mainz, Germany, around 1440 by goldsmith Johannes Gutenberg.",
        "Gutenberg synthesized durable oil-based printer inks, a handheld metal casting mold, and a modified wooden screw press.",
        "His system utilized an alloy of lead, tin, and antimony that melted at low temperatures and cast sharp typographical letterforms.",
        "His most celebrated printed achievement was the Gutenberg Bible, produced in the 1450s in a two-volume Latin edition.",
        "Before Gutenberg's invention, books in Europe were painstakingly handwritten by monastic scribes, making them exceedingly scarce.",
        "Printing technology spread rapidly across European trade routes, with presses operating in hundreds of cities by 1500.",
        "The widespread accessibility of printed texts catalyzed the Protestant Reformation by circulating Martin Luther's religious tracts.",
        "Scientific dissemination flourished as observational treatises, mathematical diagrams, and medical illustrations circulated uniformly.",
        "Increased book availability fostered widespread vernacular literacy beyond wealthy clergy and aristocratic elites.",
        "The mechanical printing press is universally regarded as one of the most transformative communication breakthroughs in human history."
    ]),
    ("panama_canal.txt", [
        "The Panama Canal is an artificial eighty-two kilometer waterway across the Isthmus of Panama connecting the Atlantic and Pacific oceans.",
        "Initial canal excavation was initiated by a private French enterprise under Ferdinand de Lesseps in 1881.",
        "The French effort collapsed financially following catastrophic worker fatalities from tropical yellow fever and malaria outbreaks.",
        "The United States acquired the canal concession in 1904 following Panamanian independence and resumed construction.",
        "Chief sanitary officer Dr. William Gorgas eradicated disease-carrying mosquito breeding vectors, making sustained labor viable.",
        "Engineers opted for a stepped gravity-fed lock system that elevates ships twenty-six meters to artificial Gatun Lake.",
        "The canal officially opened for maritime commercial navigation in August 1914 with the passage of the steamship Ancon.",
        "The transit eliminates the hazardous twelve-thousand-kilometer passage around the southern tip of South America via Cape Horn.",
        "In 1999, the United States formally transferred full administrative control of the canal to the Republic of Panama.",
        "A multi-billion dollar expansion completed in 2016 introduced wider neo-Panamax locks accommodating supersized modern vessels."
    ]),
    ("turing_test.txt", [
        "The Turing test is a test of a machine's ability to exhibit intelligent behavior equivalent to, or indistinguishable from, a human.",
        "It was originally introduced by British mathematician and cryptanalyst Alan Turing in his 1950 paper Computing Machinery and Intelligence.",
        "Turing formulated the evaluation as the Imitation Game involving a human interrogator communicating blindly via text terminal.",
        "The interrogator poses free-form questions to both a human participant and a computer program located in separate rooms.",
        "If the evaluator cannot reliably distinguish the machine from the human respondent, the machine is considered to have passed.",
        "Turing proposed this behavioral test as an operational replacement for the philosophically ambiguous question of whether machines can think.",
        "Critics such as philosopher John Searle countered with the Chinese Room thought experiment, arguing simulation does not equal understanding.",
        "Contemporary natural language processing models and conversational AI agents frequently generate human-like dialogues.",
        "Modern artificial intelligence benchmarks focus beyond conversational imitation toward rigorous task-specific reasoning capabilities.",
        "Despite philosophical debates, the Turing test remains a cornerstone concept in the foundational history of computer science."
    ]),
    ("vaccines_history.txt", [
        "The history of vaccination began scientifically in May 1796 when English physician Edward Jenner inoculated a boy with cowpox.",
        "Jenner observed that milkmaids rarely contracted deadly smallpox after having experienced benign bovine cowpox infections.",
        "His successful immunization experiments laid the formal empirical groundwork for subsequent immunological science.",
        "In the late nineteenth century, French microbiologist Louis Pasteur developed targeted vaccines against cholera, anthrax, and rabies.",
        "Pasteur introduced the principle of using attenuated or weakened pathogenic strains to generate protective host antibodies.",
        "During the mid-twentieth century, Jonas Salk and Albert Sabin developed effective polio vaccines, virtually eradicating childhood paralysis.",
        "In 1980, the World Health Assembly formally declared global smallpox eradication following an extensive worldwide vaccination campaign.",
        "Modern vaccine platforms include mRNA, recombinant viral vectors, subunit protein antigens, and inactivated pathogen formulations.",
        "Vaccination stimulates immunological memory cells without inducing the severe physiological morbidity of wild infection.",
        "Widespread community immunization creates herd immunity, protecting vulnerable individuals who cannot be medically vaccinated."
    ]),
    ("theory_of_relativity.txt", [
        "The theory of relativity comprises two interrelated physical theories formulated by theoretical physicist Albert Einstein.",
        "Special relativity, published in 1905, establishes that the laws of physics are identical for all non-accelerating inertial observers.",
        "It dictates that the speed of light in a vacuum is universally constant, regardless of the relative motion of the source.",
        "Special relativity yielded the iconic mass-energy equivalence equation E equals m c squared.",
        "It demonstrated that time dilates and lengths contract for objects traveling at relativistic fractions of light speed.",
        "General relativity, published in 1915, expanded relativity to accelerating frames and formulated a geometric theory of gravitation.",
        "Gravity is described not as an invisible Newtonian force, but as the physical curvature of four-dimensional spacetime by mass and energy.",
        "Sir Arthur Eddington confirmed general relativity in 1919 by measuring the gravitational deflection of starlight during a total solar eclipse.",
        "General relativity successfully predicted gravitational time dilation, black holes, gravitational lensing, and cosmic gravitational waves.",
        "Satellite-based Global Positioning Systems must routinely incorporate both special and general relativistic clock corrections."
    ]),
    ("periodic_table.txt", [
        "The periodic table is a tabular arrangement of chemical elements organized by increasing atomic number and recurring chemical properties.",
        "Russian chemist Dmitri Mendeleev published the first widely accepted version of the periodic table in 1869.",
        "Mendeleev arranged known elements by atomic mass and boldly left deliberate empty spaces for then-undiscovered elements.",
        "He accurately predicted the precise atomic properties of undiscovered elements including gallium, scandium, and germanium.",
        "Modern periodic tables organize elements into seven horizontal periods and eighteen vertical groups based on electron configurations.",
        "Elements residing in the same vertical group possess identical valence electron counts and exhibit similar chemical behaviors.",
        "The table categorizes elements broadly into reactive metals, transition metals, metalloids, nonmetals, halogens, and noble gases.",
        "Henry Moseley refined the table in 1913 by establishing that elements should be systematically arranged by atomic number rather than atomic weight.",
        "Currently, the periodic table contains 118 formally confirmed chemical elements, completing the first seven periods.",
        "The periodic system remains the indispensable organizational framework of chemical synthesis, pedagogy, and materials science."
    ])
]

for fname, lines in medium_txt_data:
    make_txt(fname, lines)

# Medium PDFs
medium_pdf_data = [
    ("antibiotics_history.pdf", "The Development and Impact of Antibiotics", [
        "Antibiotics are antimicrobial substances active against bacteria and are the most important type of antibacterial agent for fighting bacterial infections.",
        "Alexander Fleming's 1928 discovery of penicillin heralded the modern antibiotic era, but large-scale purification occurred in the early 1940s.",
        "Howard Florey and Ernst Chain at Oxford University successfully isolated stable penicillin and demonstrated its curative power in human clinical trials.",
        "Mass production during World War II saved tens of thousands of wounded Allied military personnel from fatal bacterial wound infections.",
        "Subsequent discoveries in the 1940s and 1950s yielded streptomycin, chloramphenicol, tetracyclines, and macrolide antibiotic classes.",
        "Antibiotics function through diverse mechanisms, including inhibiting bacterial cell wall synthesis, disrupting protein translation, or blocking DNA replication.",
        "Widespread clinical overuse and agricultural feeding have accelerated the emergence of resistant superbug bacterial strains.",
        "Pathogens such as methicillin-resistant Staphylococcus aureus present serious challenges in hospital and critical care environments.",
        "Contemporary pharmaceutical research seeks novel antimicrobial targets and bacteriophage therapies to overcome resistance pathways."
    ]),
    ("semiconductors_intro.pdf", "Fundamentals of Semiconductor Technology", [
        "A semiconductor is a crystalline material whose electrical conductivity lies between that of a conductor and an insulator.",
        "Silicon is the primary chemical element utilized in commercial semiconductor fabrication due to its high elemental abundance and stable oxide.",
        "The electrical properties of semiconductors are precisely tailored through doping, introducing tiny quantities of donor or acceptor impurities.",
        "N-type semiconductors are doped with elements providing mobile conduction electrons, whereas p-type semiconductors possess excess electron holes.",
        "The junction where p-type and n-type semiconductor regions meet forms a p-n junction, the building block of diodes and solar cells.",
        "In 1947, John Bardeen, Walter Brattain, and William Shockley invented the point-contact bipolar transistor at Bell Laboratories.",
        "Transistors superseded fragile vacuum tubes, enabling compact, energy-efficient electronic signal amplification and switching.",
        "The planar integrated circuit was independently developed in the late 1950s by Jack Kilby and Robert Noyce, integrating components on single chips.",
        "Photolithographic techniques continually shrink transistor gate lengths, enabling billions of transistors on modern microprocessors.",
        "Semiconductor chips power modern computers, smartphones, medical monitoring hardware, electric vehicles, and telecommunication satellites."
    ]),
    ("renaissance_masters.pdf", "Master Artists and Polymaths of the Italian Renaissance", [
        "The Italian Renaissance catalyzed unprecedented artistic innovations in linear perspective, naturalistic anatomy, and chiaroscuro illumination.",
        "Leonardo da Vinci represented the archetypal Renaissance man, excelling across fine art, military engineering, hydrodynamics, and anatomical dissection.",
        "Leonardo's mural The Last Supper in Milan and portrait Mona Lisa in the Louvre are celebrated worldwide for psychological subtlety and sfumato technique.",
        "Michelangelo Buonarroti demonstrated supreme mastery in marble sculpture, carving the Pieta in St. Peter's Basilica at just twenty-four years of age.",
        "Commissioned by Pope Julius II, Michelangelo spent four arduous years painting the expansive fresco program across the Sistine Chapel ceiling.",
        "Raffaello Sanzio, known as Raphael, painted the School of Athens fresco in the Apostolic Palace, portraying classical Greek philosophers in debate.",
        "Venetian painter Titian pioneered rich oil glazing methods that established coloristic traditions influencing generations of European painters.",
        "Architect Andrea Palladio synthesized classical Roman proportions into symmetrical villa designs that profoundly influenced neoclassical architecture.",
        "Giorgio Vasari documented the achievements of contemporary masters in his monumental biographical publication Lives of the Artists in 1550.",
        "The artistic legacy of the Renaissance transformed aesthetic philosophy and permanently redefined the societal standing of visual artists."
    ]),
    ("electromagnetism_principles.pdf", "Foundations of Classical Electromagnetism", [
        "Classical electromagnetism is the branch of theoretical physics that investigates the interactions between electric charges and currents.",
        "In 1820, Danish physicist Hans Christian Oersted discovered that an electric current flowing through a wire deflects a nearby magnetic compass needle.",
        "Shortly thereafter, Andre-Marie Ampere formulated mathematical relationships describing the magnetic forces exerted between current-carrying conductors.",
        "In 1831, Michael Faraday discovered electromagnetic induction, demonstrating that a fluctuating magnetic field induces an electromotive force in a conductor.",
        "Faraday's discovery established the foundational physical principle governing electric generators, transformers, and industrial electric motors.",
        "Scottish physicist James Clerk Maxwell unified electricity and magnetism in the 1860s into a set of four partial differential equations.",
        "Maxwell's equations demonstrated that oscillating electric and magnetic fields propagate together through space as self-sustaining transverse waves.",
        "Maxwell calculated that these electromagnetic waves travel at the speed of light, leading to the profound realization that light itself is an electromagnetic wave.",
        "In the late 1880s, Heinrich Hertz experimentally produced and detected radio waves in his laboratory, confirming Maxwell's theoretical predictions.",
        "Electromagnetic principles govern modern wireless telecommunications, radar, electrical power grids, and optical instruments."
    ]),
    ("microbiology_history.pdf", "Pioneers and Discoveries in Microbiology", [
        "Microbiology is the scientific study of microscopic living organisms, including bacteria, viruses, fungi, protozoa, and microscopic algae.",
        "Dutch draper Antonie van Leeuwenhoek is celebrated as the father of microbiology after constructing high-magnification single-lens microscopes.",
        "In the 1670s, Leeuwenhoek documented the existence of single-celled microorganisms in pond water and dental scrapings, calling them animalcules.",
        "For nearly two centuries, scientific doctrine debated spontaneous generation, the belief that living organisms regularly emerge from non-living matter.",
        "Louis Pasteur conclusively disproved spontaneous generation in the 1860s using swan-neck flasks that permitted air while excluding airborne dust.",
        "Pasteur developed pasteurization, a controlled heating process killing spoilage organisms in wine, beer, and dairy products.",
        "German physician Robert Koch established formal experimental criteria, Koch's postulates, to prove a specific microbe causes a specific disease.",
        "Koch identified the causative bacterial agents of tuberculosis, cholera, and anthrax, earning the 1905 Nobel Prize in Physiology or Medicine.",
        "English surgeon Joseph Lister introduced antiseptic surgical methods using carbolic acid phenol sprays to prevent post-operative gangrene.",
        "Microbiology established the germ theory of disease, revolutionizing public hygiene, hospital protocols, and infectious disease control."
    ])
]

for fname, title, paras in medium_pdf_data:
    make_pdf(fname, title, paras)

# ==============================================================================
# 3. COMPREHENSIVE DEEP-DIVE DOCUMENTS (At least 100 lines each)
# ==============================================================================
def generate_long_doc_text(topic_name: str, domain: str, key_facts: list[str]) -> list[str]:
    """Generates a structured, multi-section comprehensive document of 105+ lines."""
    lines = [
        f"# COMPREHENSIVE TREATISE: {topic_name.upper()}",
        f"Domain: {domain} | Reference Documentation and Field Manual",
        "=" * 80,
        "",
        "## SECTION 1: HISTORICAL BACKGROUND AND EARLY DEVELOPMENTS",
        f"The comprehensive study of {topic_name} represents a milestone in the development of {domain}.",
        "For centuries, researchers, scholars, and field practitioners sought empirical frameworks to explain core phenomena.",
        "Early historical observations laid the groundwork for systematic inquiry and formal classification.",
    ]
    for i in range(1, 15):
        lines.append(f"Historical record {i}: Early foundational inquiries into {topic_name} provided preliminary models.")
        lines.append(f"Scholars debated theoretical interpretations and cataloged observational anomalies systematically.")
    
    lines.extend([
        "",
        "## SECTION 2: FUNDAMENTAL PRINCIPLES AND SCIENTIFIC MECHANISMS",
        f"Understanding {topic_name} requires examining its core operational mechanisms and physical laws.",
    ])
    for fact in key_facts:
        lines.append(f"CORE FACT: {fact}")
        lines.append(f"Empirical validation confirms that {fact.lower()}")
    
    for i in range(1, 15):
        lines.append(f"Mechanism detail {i}: The internal dynamics of {topic_name} demonstrate measurable consistency.")
        lines.append(f"Experimental tests across independent laboratories have continuously substantiated these baseline parameters.")

    lines.extend([
        "",
        "## SECTION 3: SYSTEM ARCHITECTURE AND DETAILED TAXONOMY",
        f"A thorough taxonomy of {topic_name} classifies entities according to functional properties and structural hierarchies.",
    ])
    for i in range(1, 18):
        lines.append(f"Classification tier {i}: Specific taxonomic subsets within {topic_name} display distinct characteristics.")
        lines.append(f"Sub-category {i} exhibits specialized interactions with environmental and systemic variables.")

    lines.extend([
        "",
        "## SECTION 4: CONTEMPORARY APPLICATIONS AND ENGINEERING IMPACT",
        f"Modern applications of {topic_name} span diverse sectors including industrial manufacturing, computational modeling, and research.",
    ])
    for i in range(1, 15):
        lines.append(f"Application vector {i}: Contemporary engineers apply principles of {topic_name} to optimize real-world operations.")
        lines.append(f"Standard operational protocols ensure rigorous safety, reproducibility, and high fidelity performance.")

    lines.extend([
        "",
        "## SECTION 5: METHODOLOGICAL STANDARDS AND FUTURE PROSPECTS",
        f"Rigorous analytical standards govern ongoing investigations into {topic_name}.",
        "Current academic consortia emphasize cross-disciplinary collaboration to unlock next-generation capabilities.",
    ])
    for i in range(1, 12):
        lines.append(f"Future outlook {i}: Emerging instrumentation will enhance observational precision regarding {topic_name}.")
        lines.append(f"Prospective field trials continue to validate theoretical extrapolations under extreme boundary conditions.")

    lines.extend([
        "",
        "## SECTION 6: CONCLUDING SYNTHESIS AND CORE CITATIONS",
        f"In summary, {topic_name} remains an indispensable pillar of modern {domain}.",
        "Full documentation, empirical records, and experimental registries are maintained for continued academic verification.",
        "End of comprehensive reference document."
    ])
    return lines

long_doc_configs = [
    ("long_history_of_computing.txt", "History of Computing and Architecture", "Computer Science", [
        "Charles Babbage designed the mechanical Analytical Engine in the 1830s with Ada Lovelace writing the first algorithm.",
        "ENIAC, completed in 1945 at the University of Pennsylvania, was the first programmable general-purpose electronic digital computer.",
        "The von Neumann architecture describes a system structure where program instructions and data share the same unified memory space.",
        "The invention of the silicon microchip in 1958 enabled dramatic reductions in physical size and operational power consumption."
    ]),
    ("long_astronomy_handbook.txt", "Modern Observational Astronomy Handbook", "Astrophysics", [
        "The Milky Way galaxy is a barred spiral galaxy containing an estimated 100 to 400 billion stars.",
        "Supernovae are energetic stellar explosions that synthesize and distribute heavy elements throughout interstellar space.",
        "Neutron stars are extremely dense stellar remnants composed almost entirely of closely packed neutrons.",
        "The cosmic microwave background radiation is thermal relic radiation dating from approximately 380,000 years after the Big Bang."
    ]),
    ("long_cell_biology_principles.txt", "Comprehensive Cellular Biology and Physiology", "Life Sciences", [
        "The cell theory states that all living organisms are composed of one or more cells, the fundamental unit of life.",
        "Cellular respiration in the presence of oxygen breaks down glucose to yield approximately 30 to 32 ATP molecules.",
        "Ribosomes are ribonucleoprotein complexes responsible for translating messenger RNA transcripts into polypeptide proteins.",
        "The phospholipid bilayer of the cell membrane possesses hydrophilic outer heads and hydrophobic inner fatty acid tails."
    ]),
    ("long_thermodynamics_foundations.txt", "Foundations of Classical and Statistical Thermodynamics", "Thermal Physics", [
        "The zeroth law of thermodynamics defines temperature and establishes thermal equilibrium as an equivalence relation.",
        "The first law of thermodynamics states that the total internal energy of an isolated system remains strictly conserved.",
        "The second law asserts that the total entropy of an isolated thermodynamic system can never decrease over time.",
        "The third law establishes that the entropy of a pure crystalline substance approaches zero as temperature approaches absolute zero."
    ]),
    ("long_modern_cryptography.txt", "Principles of Modern Cryptography and Data Security", "Information Security", [
        "Symmetric encryption utilizes the same shared secret key for both data encryption and subsequent data decryption.",
        "Public-key asymmetric cryptography utilizes mathematically linked pairs of public and private keys, as introduced by RSA in 1977.",
        "Cryptographic hash functions generate fixed-length deterministic digests that are computationally infeasible to invert.",
        "The Advanced Encryption Standard (AES) was established by NIST in 2001 utilizing Rijndael block cipher specifications."
    ]),
    ("long_world_war_one.txt", "Military and Political History of World War I", "Modern History", [
        "World War I was a global military conflict centered in Europe that lasted from July 1914 until November 1918.",
        "The assassination of Archduke Franz Ferdinand of Austria in Sarajevo in June 1914 precipitated the crisis.",
        "The Western Front was characterized by protracted trench warfare, barbed wire entanglements, and poison gas deployments.",
        "The Treaty of Versailles, signed in June 1919, officially ended the state of war between Germany and the Allied Powers."
    ]),
    ("long_climate_science.txt", "Earth Climate Systems and Atmospheric Dynamics", "Earth Systems", [
        "The natural greenhouse effect traps thermal infrared radiation emitted from Earth's surface, maintaining habitability.",
        "Atmospheric carbon dioxide concentrations have risen from pre-industrial levels of 280 ppm to over 420 ppm today.",
        "Global surface ocean temperatures have absorbed more than ninety percent of accumulated planetary excess heat.",
        "Thermohaline circulation acts as a global ocean conveyor belt driven by water density, temperature, and salinity gradients."
    ]),
    ("long_neuroscience_fundamentals.txt", "Fundamentals of Human Neuroscience and Cognition", "Medical Science", [
        "The human nervous system contains an estimated 86 billion neurons interconnected by trillions of synaptic junctions.",
        "Action potentials are rapid electrical membrane depolarizations mediated by voltage-gated sodium and potassium channels.",
        "Neurotransmitters such as dopamine, serotonin, and acetylcholine transmit signals chemical across synaptic clefts.",
        "The cerebral cortex is divided into frontal, parietal, temporal, and occipital lobes supporting specialized cognition."
    ]),
    ("long_ancient_greece.txt", "Civilization and Philosophy of Ancient Greece", "Classical History", [
        "Classical Athens developed the world's first documented direct democracy during the fifth century BC under Pericles.",
        "Socrates developed the elenctic dialectical method of inquiry, emphasizing critical questioning of moral assumptions.",
        "Plato founded the Academy in Athens around 387 BC and authored foundational dialogues including The Republic.",
        "Aristotle established the Lyceum and made pioneering contributions to formal logic, biology, ethics, and metaphysics."
    ]),
    ("long_inorganic_chemistry.txt", "Principles and Reactions in Inorganic Chemistry", "Chemical Sciences", [
        "Covalent chemical bonds involve the mutual sharing of valence electron pairs between bonding atomic nuclei.",
        "Ionic bonds form through the complete electrostatic transfer of electrons between electropositive and electronegative atoms.",
        "Transition metals exhibit variable oxidation states, catalytic activity, and colorful coordinate complex geometries.",
        "Acid-base chemistry is modeled by Bronsted-Lowry proton transfer reactions and Lewis electron pair donor-acceptor interactions."
    ]),
    ("long_genetics_and_heredity.txt", "Principles of Classical and Molecular Genetics", "Genetics", [
        "Gregor Mendel established the fundamental laws of inheritance through empirical pea plant hybridization experiments in 1865.",
        "Mendel's law of segregation states that alleles for each trait separate during gamete formation so each gamete carries one allele.",
        "Genes are discrete physical segments of DNA located at specific loci along homologous eukaryotic chromosomes.",
        "The central dogma of molecular biology dictates that genetic information typically flows from DNA to RNA to protein."
    ]),
    ("long_renaissance_literature.txt", "Survey of Renaissance and Early Modern Literature", "Literary Studies", [
        "William Shakespeare wrote thirty-nine plays and 154 sonnets, transforming English dramatic literature in the Elizabethan era.",
        "Miguel de Cervantes published Don Quixote in two parts in 1605 and 1615, widely considered the first modern Western novel.",
        "Dante Alighieri's Divine Comedy, written in fourteenth-century Italian vernacular, established epic tripartite cosmological structure.",
        "Geoffrey Chaucer's Canterbury Tales provided a diverse cross-sectional panoramic portrait of medieval English society."
    ]),
    ("long_materials_science.txt", "Advanced Materials Science and Solid State Physics", "Materials Engineering", [
        "Graphene is a single two-dimensional planar sheet of carbon atoms bonded in a hexagonal honeycomb crystal lattice.",
        "Superconductors exhibit zero electrical resistance and complete expulsion of internal magnetic fields below critical temperatures.",
        "Carbon nanotubes possess exceptional tensile strength, thermal conductivity, and ballistic electronic transport properties.",
        "Metamaterials are engineered artificial composite structures designed to exhibit negative refractive indices and optical cloaking."
    ]),
    ("long_microeconomics_theory.txt", "Principles of Microeconomic Analysis and Markets", "Economic Sciences", [
        "The law of supply and demand dictates that competitive market clearing prices equate quantity supplied with quantity demanded.",
        "Elasticity measures the proportional responsiveness of quantity demanded or supplied to changes in price or consumer income.",
        "Monopolistic market structures feature single sellers facing high barriers to entry, producing deadweight economic losses.",
        "Game theory analyzes strategic interactive decision-making, formalized by the concept of the Nash equilibrium."
    ]),
    ("long_geology_earth_structure.txt", "Internal Geophysics and Structure of Earth", "Geophysical Sciences", [
        "The Earth is layered into a silicate solid crust, a viscous semi-solid mantle, a liquid outer core, and a solid iron-nickel inner core.",
        "Seismic P-waves are longitudinal compressional waves that travel through both solid rock and liquid planetary layers.",
        "Seismic S-waves are transverse shear waves that cannot propagate through liquids, proving the Earth's outer core is liquid.",
        "The geomagnetic field is generated through a self-sustaining geodynamo driven by convective fluid motion in the liquid iron outer core."
    ]),
    ("long_fluid_mechanics.txt", "Fundamentals of Classical Fluid Mechanics and Aerodynamics", "Mechanical Engineering", [
        "Bernoulli's principle states that an increase in the speed of a fluid occurs simultaneously with a decrease in static pressure.",
        "The Navier-Stokes equations are fundamental non-linear partial differential equations describing the motion of viscous fluids.",
        "Laminar fluid flow is characterized by smooth, parallel fluid layers exhibiting minimal lateral mixing or chaotic turbulence.",
        "The Reynolds number is a dimensionless quantity measuring the ratio of inertial forces to viscous forces in fluid flow."
    ]),
    ("long_immunology_handbook.txt", "Comprehensive Principles of Human Immunology", "Immunology", [
        "The innate immune system provides immediate non-specific host defense through anatomical barriers and phagocytic white blood cells.",
        "The adaptive immune system provides antigen-specific memory mediated by antibody-producing B lymphocytes and T lymphocytes.",
        "Antibodies, or immunoglobulins, are Y-shaped proteins that bind specifically to foreign pathogenic antigen epitopes.",
        "The major histocompatibility complex (MHC) molecules present peptide fragments on cell surfaces for T cell receptor recognition."
    ]),
    ("long_botany_plant_physiology.txt", "Principles of Botany and Plant Physiological Systems", "Plant Biology", [
        "Xylem tissue transports water and dissolved inorganic minerals upward from roots through capillary action and transpirational pull.",
        "Phloem tissue translocates synthesized organic photoassimilates and sucrose bidirectionally via pressure-flow bulk transport.",
        "Stomata are specialized microscopic pore complexes on leaves regulated by guard cells to balance carbon dioxide intake with water loss.",
        "Plant growth and phototropic orientations are regulated by hormonal signaling cascades including auxins, gibberellins, and abscisic acid."
    ]),
    ("long_astrophysics_stellar_evolution.txt", "Stellar Structure Evolution and Nucleosynthesis", "Astrophysics", [
        "Main-sequence stars generate internal energy through the thermonuclear fusion of hydrogen nuclei into helium in their cores.",
        "The Sun converts approximately 600 million tons of hydrogen into helium every second via the proton-proton chain reaction.",
        "The Chandrasekhar limit of approximately 1.4 solar masses defines the maximum theoretical mass of a stable white dwarf star.",
        "Stars exceeding eight solar masses conclude their evolution through core-collapse gravitational supernovae, leaving neutron stars or black holes."
    ]),
    ("long_ecology_ecosystem_dynamics.txt", "Ecology Population Dynamics and Biome Structures", "Environmental Biology", [
        "Ecosystems consist of biological communities of interacting organisms and their physical abiotic environment.",
        "Trophic levels structure ecological food webs, with roughly ten percent of energy successfully transferred between adjacent feeding tiers.",
        "Keystone species exert disproportionately large regulatory impacts on community biodiversity relative to their physical abundance.",
        "Biogeochemical cycles continuously recycle critical chemical elements including carbon, nitrogen, phosphorus, and water through the biosphere."
    ])
]

# Write long TXT documents
for fname, title, domain, facts in long_doc_configs:
    lines = generate_long_doc_text(title, domain, facts)
    make_txt(fname, lines)

# Write long PDF documents (multi-page, 100+ lines of text rendered)
long_pdf_configs = [
    ("long_treatise_quantum_physics.pdf", "Comprehensive Treatise on Quantum Mechanics and Applications", [
        "Quantum mechanics is the mathematical foundation of atomic physics, chemistry, and condensed matter.",
        "Wave functions represent probability amplitudes whose absolute squared magnitude defines spatial probability density.",
        "The Copenhagen interpretation postulates that measurement induces an instantaneous state reduction or wave function collapse.",
        "Quantum entanglement describes non-local correlations between particles that cannot be explained by classical local hidden variables.",
        "Bell's theorem proved experimentally that quantum mechanics violates local realism, confirming non-classical correlations.",
        "Quantum tunneling allows particles to traverse finite potential energy barriers that would be impassable in classical mechanics.",
        "The Pauli exclusion principle dictates that identical fermions cannot simultaneously occupy identical quantum states.",
        "This exclusion principle prevents atomic collapse and explains the structural shell periodicity of the chemical elements."
    ] + [f"Detailed quantum analysis paragraph {i}: Advanced perturbation theory and matrix mechanics formulate Hamiltonian eigenvalues with empirical precision." for i in range(1, 35)]),

    ("long_encyclopedia_world_history.pdf", "Encyclopedia of Global Civilizations and Transformations", [
        "The agricultural Neolithic Revolution around 10,000 BC initiated permanent sedentary settlements and social stratification.",
        "Cuneiform writing developed in ancient Sumer around 3400 BC, recording commercial inventories and legal codes.",
        "The Silk Road was an expansive transcontinental network of Eurasian overland trade routes linking China with the Mediterranean.",
        "The Black Death pandemic of the mid-fourteenth century decimated roughly one-third to half of the European population.",
        "The Age of Exploration initiated direct maritime global trade networks and widespread biological Columbian exchange.",
        "The Peace of Westphalia in 1648 established foundational doctrines of sovereign state equality in modern international law.",
        "The Meiji Restoration of 1868 catalyzed accelerated industrialization and modernization throughout the Empire of Japan.",
        "The United Nations was chartered in 1945 in San Francisco following World War II to maintain international peace."
    ] + [f"Historical analysis paragraph {i}: Geopolitical shifts and diplomatic alliances continuously transformed global balance-of-power architectures." for i in range(1, 35)]),

    ("long_handbook_molecular_biology.pdf", "Comprehensive Handbook of Molecular Biology and Biotechnology", [
        "Recombinant DNA technology allows deliberate molecular joining of genetic sequences from diverse biological species.",
        "Restriction endonucleases are bacterial enzymes that recognize and cleave foreign DNA at specific palindromic sequences.",
        "Polymerase chain reaction (PCR) developed by Kary Mullis in 1983 enables exponential in vitro amplification of DNA fragments.",
        "Gel electrophoresis separates nucleic acid fragments and proteins based on electrical charge and molecular weight hydrodynamic migration.",
        "Sanger dideoxy sequencing established the initial enzymatic method for determining exact nucleotide order in DNA strands.",
        "Next-generation massively parallel sequencing platforms generate gigabases of genomic sequence data within hours.",
        "Plasmids are small circular extrachromosomal DNA molecules widely employed as molecular cloning vectors in biotechnology.",
        "Monoclonal antibodies produced via hybridoma technology provide targeted therapeutic agents in oncology and rheumatology."
    ] + [f"Biotechnology laboratory protocol {i}: Standard operating procedures require calibrated enzymatic concentrations and sterile buffer preparations." for i in range(1, 35)]),

    ("long_principles_of_organic_chemistry.pdf", "Advanced Principles and Mechanisms of Organic Chemistry", [
        "Organic chemistry is the systematic scientific discipline studying the structure, properties, and reactions of carbon compounds.",
        "Carbon exhibits unique catenation capabilities, forming stable single, double, and triple covalent bonds with varied elements.",
        "Hydrocarbons are organic chemical molecules composed exclusively of carbon and hydrogen atoms in aliphatic or aromatic arrangements.",
        "Alkanes are saturated hydrocarbons possessing only single covalent bonds, conforming to the general formula CnH2n+2.",
        "Alkenes contain at least one carbon-carbon double bond, whereas alkynes possess at least one carbon-carbon triple bond.",
        "Aromatic compounds such as benzene exhibit exceptional cyclic delocalized resonance stability conforming to Huckel's 4n+2 rule.",
        "Functional groups including alcohols, aldehydes, ketones, carboxylic acids, and amines determine characteristic chemical reactivity.",
        "Nucleophilic substitution reactions proceed via unimolecular SN1 or concerted bimolecular SN2 mechanistic pathways."
    ] + [f"Reaction mechanism analysis {i}: Stereochemical inversions and transition state free energies dictate kinetic versus thermodynamic product ratios." for i in range(1, 35)]),

    ("long_earth_geological_history.pdf", "Geological History and Stratigraphy of Planet Earth", [
        "Earth's geological history is divided into four major eons: the Hadean, Archean, Proterozoic, and Phanerozoic.",
        "The Hadean eon spans from planetary accretion 4.54 billion years ago until the formation of the earliest stable rock crusts.",
        "The Great Oxidation Event approximately 2.4 billion years ago introduced biogenic free oxygen into Earth's atmosphere.",
        "The Cambrian explosion roughly 541 million years ago witnessed an unprecedented evolutionary diversification of complex animal phyla.",
        "The Permian-Triassic extinction event 252 million years ago was Earth's most severe extinction, eliminating over ninety percent of species.",
        "Dinosaurs flourished throughout the Mesozoic era across the Triassic, Jurassic, and Cretaceous geological periods.",
        "The Cretaceous-Paleogene extinction 66 million years ago was caused by a massive asteroid impact at the Chicxulub crater in Mexico.",
        "The Cenozoic era witnessed the dramatic adaptive radiation of mammals and birds, culminating in the Quaternary emergence of hominids."
    ] + [f"Stratigraphic correlation record {i}: Sedimentary rock strata and index fossil horizons document past paleoenvironmental transitions." for i in range(1, 35)])
]

for fname, title, paras in long_pdf_configs:
    make_pdf(fname, title, paras)

print(f"\nSuccessfully generated complete corpus in {DOC_DIR}!")

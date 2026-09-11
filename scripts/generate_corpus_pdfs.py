"""
Generate authoritative healthcare PDF documents for the RAG knowledge corpus.
Sources: NIH Office of Dietary Supplements (ODS), CDC, WHO, MedlinePlus, USDA/HHS.
"""

import os
import pymupdf

DOCS_DIR = "data/documents"
os.makedirs(DOCS_DIR, exist_ok=True)


def create_pdf(filename: str, pages_content: list[tuple[str, str]]) -> None:
    """Creates a multi-page PDF document using PyMuPDF.

    Args:
        filename: Destination filename inside data/documents.
        pages_content: List of tuples (header_title, body_text) for each page.
    """
    file_path = os.path.join(DOCS_DIR, filename)
    doc = pymupdf.open()

    for idx, (header, body) in enumerate(pages_content, 1):
        page = doc.new_page(width=612, height=792)  # Standard Letter size
        
        # Header text
        header_text = f"{header}  -  Page {idx}\n" + ("=" * 70)
        page.insert_text((54, 54), header_text, fontsize=11, fontname="helv", color=(0.1, 0.3, 0.4))
        
        # Body text area
        rect = pymupdf.Rect(54, 80, 558, 738)
        page.insert_textbox(rect, body.strip(), fontsize=10.5, fontname="helv", color=(0.1, 0.1, 0.1), lineheight=1.4)

    doc.save(file_path)
    doc.close()
    print(f"Created '{filename}' with {len(pages_content)} pages.")


def generate_all():
    # 1. NIH ODS Boron Fact Sheet
    create_pdf(
        "nih_ods_boron.pdf",
        [
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Boron",
                """Overview and Essentiality:
Boron is a chemical element that is present naturally in many foods and is available as a dietary supplement. It is not currently classified as an essential nutrient for humans because a clear biological function has not been established. However, evidence suggests that boron may influence the metabolism of other minerals, including calcium, magnesium, and phosphorus, and may play a role in bone maintenance and steroid hormone activity.

Dietary Sources of Boron:
Plant foods are the primary dietary sources of boron. High concentrations of boron are found in fruits, fruit juices, nuts, and legumes:
- Fruits: Avocados, red grapes, raisins, peaches, apples, and pears.
- Nuts and Legumes: Peanuts, almonds, hazelnuts, kidney beans, and lentils.
- Beverages: Wine, cider, and beer also contribute to boron intake in adult diets.
Animal-derived foods (meat, poultry, fish, and dairy) are relatively low in boron. Most adults in the United States consume approximately 1 mg of boron per day through a standard diet.

Biological Roles:
Studies indicate that boron interacts with vitamin D, steroid hormones (such as estrogen and testosterone), and cellular antioxidant defenses. Boron supplements are commercially available as boron citrate, boron glycinate, boron aspartate, and calcium fructoborate."""
            ),
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Boron",
                """Tolerable Upper Intake Levels (UL) for Boron:
The Food and Nutrition Board (FNB) of the National Academies established Tolerable Upper Intake Levels (ULs) for boron for the general population. The UL is the highest level of daily intake that is likely to pose no risk of adverse health effects in almost all individuals:

Age Group and Tolerable Upper Intake Level (UL):
- Birth to 12 months: Not established (intake should be from breast milk, formula, and food)
- Children 1-3 years: 3 mg/day
- Children 4-8 years: 6 mg/day
- Children 9-13 years: 11 mg/day
- Adolescents 14-18 years: 17 mg/day
- Adults 19 years and older: 20 mg/day (including pregnant and lactating females)

Health Risks of Excessive Boron:
The UL for boron was established based on animal studies showing adverse effects on male reproduction and embryonic development. In humans, acute ingestion of high doses of boron (such as boric acid) can cause nausea, gastrointestinal discomfort, vomiting, diarrhea, dermatitis, and lethargy. Chronic excessive intake above the 20 mg/day adult upper limit is not recommended."""
            ),
        ]
    )

    # 2. NIH ODS Vitamin B12 Fact Sheet
    create_pdf(
        "nih_ods_vitamin_b12.pdf",
        [
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Vitamin B12",
                """Overview and Biological Roles:
Vitamin B12 (cobalamin) is a water-soluble vitamin that is naturally present in some foods, added to others, and available as a dietary supplement. Vitamin B12 is essential for:
- Red blood cell formation and erythropoiesis
- Neurological function and maintenance of the myelin sheath
- DNA synthesis and homocysteine regulation (working as a cofactor with folate)

Recommended Dietary Allowances (RDA) for Vitamin B12:
The Food and Nutrition Board established the following daily RDAs:
- Infants 0-6 months: 0.4 mcg (Adequate Intake)
- Infants 7-12 months: 0.5 mcg (Adequate Intake)
- Children 1-3 years: 0.9 mcg/day
- Children 4-8 years: 1.2 mcg/day
- Children 9-13 years: 1.8 mcg/day
- Adolescents and Adults 14+ years: 2.4 mcg/day
- Pregnant Females: 2.6 mcg/day
- Lactating Females: 2.8 mcg/day

Tolerable Upper Intake Level (UL):
The FNB has not established a UL for vitamin B12 because of its low potential for toxicity. Excess amounts are typically excreted in urine."""
            ),
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Vitamin B12",
                """Food Sources of Vitamin B12:
Vitamin B12 is naturally found primarily in foods of animal origin:
- Fish and Seafood: Clams, oysters, salmon, trout, and tuna.
- Meat and Poultry: Beef liver, beef, and turkey.
- Dairy and Eggs: Milk, yogurt, cheese, and eggs.
- Fortified Foods: Fortified breakfast cereals and nutritional yeasts are critical sources for vegetarians and vegans. Unfortified plant foods contain no vitamin B12.

Absorption Mechanisms:
Absorption of vitamin B12 requires gastric hydrochloric acid to release the vitamin from food protein, and intrinsic factor (secreted by gastric parietal cells) to facilitate ileal absorption. Individuals with atrophic gastritis, pernicious anemia, or previous gastric bypass surgery have impaired absorption.

Deficiency Manifestations:
Vitamin B12 deficiency leads to megaloblastic anemia, fatigue, weakness, constipation, and loss of appetite. Neurological symptoms include numbness and tingling in the hands and feet (peripheral neuropathy), difficulty walking, balance problems, memory loss, and depression. Neurological damage can become permanent if untreated."""
            ),
        ]
    )

    # 3. NIH ODS Folate Fact Sheet
    create_pdf(
        "nih_ods_folate.pdf",
        [
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Folate",
                """Overview and Function:
Folate is a water-soluble B-vitamin (vitamin B9) that is naturally present in foods. Folic acid is the synthetic form of folate used in fortified foods and most dietary supplements. Folate functions as a coenzyme in the synthesis of nucleic acids (DNA and RNA) and in the metabolism of amino acids, including the conversion of homocysteine to methionine.

Recommended Dietary Allowances (RDA) in Dietary Folate Equivalents (DFE):
The FNB established the following RDAs:
- Children 1-3 years: 150 mcg DFE/day
- Children 4-8 years: 200 mcg DFE/day
- Children 9-13 years: 300 mcg DFE/day
- Adolescents 14-18 years: 400 mcg DFE/day
- Adults 19+ years: 400 mcg DFE/day
- Pregnant Females: 600 mcg DFE/day
- Lactating Females: 500 mcg DFE/day

Neural Tube Defect Prevention:
Adequate folate intake is critical prior to conception and during early pregnancy. Periconceptional intake of 400 to 800 mcg of folic acid daily substantially reduces the risk of neural tube defects, specifically spina bifida and anencephaly."""
            ),
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Folate",
                """Dietary Sources of Folate:
Folate is found naturally in a wide variety of plant foods:
- Dark Green Leafy Vegetables: Spinach, kale, Brussels sprouts, and asparagus.
- Legumes and Nuts: Black-eyed peas, kidney beans, peanuts, and sunflower seeds.
- Fruits: Oranges, orange juice, papayas, and bananas.
- Fortified Foods: In the United States, enriched grains (flour, bread, rice, pasta, and cornmeal) are mandated to be fortified with folic acid (140 mcg per 100 g).

Tolerable Upper Intake Level (UL):
The UL for folate applies ONLY to synthetic folic acid from fortified foods and supplements, not natural food folate:
- Children 1-3 years: 300 mcg DFE/day
- Children 4-8 years: 400 mcg DFE/day
- Children 9-13 years: 600 mcg DFE/day
- Adolescents 14-18 years: 800 mcg DFE/day
- Adults 19+ years: 1,000 mcg DFE/day

High intakes of folic acid can mask the hematologic signs of vitamin B12 deficiency while allowing neurological damage to progress."""
            ),
        ]
    )

    # 4. NIH ODS Vitamin D Fact Sheet
    create_pdf(
        "nih_ods_vitamin_d.pdf",
        [
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Vitamin D",
                """Overview and Skeletal Role:
Vitamin D (calciferol) is a fat-soluble vitamin that promotes calcium absorption in the gut and maintains adequate serum calcium and phosphate concentrations to enable normal bone mineralization. It is also needed for bone growth and bone remodeling by osteoblasts and osteoclasts. Without sufficient vitamin D, bones can become thin, brittle, or misshapen.

Recommended Dietary Allowances (RDA) for Vitamin D:
- Infants 0-12 months: 400 IU (10 mcg) daily (Adequate Intake)
- Children and Adults 1-70 years: 600 IU (15 mcg) daily (includes pregnant and lactating females)
- Adults 71 years and older: 800 IU (20 mcg) daily

Tolerable Upper Intake Levels (UL) for Vitamin D:
The FNB established the following ULs:
- Infants 0-6 months: 1,000 IU (25 mcg) daily
- Infants 7-12 months: 1,500 IU (37.5 mcg) daily
- Children 1-3 years: 2,500 IU (62.5 mcg) daily
- Children 4-8 years: 3,000 IU (75 mcg) daily
- Children 9+ and Adults: 4,000 IU (100 mcg) daily"""
            ),
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Vitamin D",
                """Sources of Vitamin D:
- Cutaneous Synthesis: The body synthesizes vitamin D3 in the skin when exposed to ultraviolet B (UVB) radiation from sunlight. Season, latitude, air pollution, cloud cover, and melanin affect synthesis.
- Dietary Sources: Few foods naturally contain vitamin D. The best natural sources are flesh of fatty fish (such as trout, salmon, tuna, and mackerel) and fish liver oils. Beef liver, egg yolks, and cheese contain small amounts.
- Fortified Foods: In the U.S. food supply, fortified foods provide most dietary vitamin D, including fortified cow milk, fortified plant milk alternatives, infant formula, and fortified breakfast cereals.

Deficiency and Toxicity:
In children, severe vitamin D deficiency leads to rickets (failure of bone tissue to properly mineralize, resulting in soft bones and skeletal deformities). In adults, deficiency leads to osteomalacia and exacerbates osteoporosis. Excessive intake causes hypercalcemia, renal impairment, and vascular calcification."""
            ),
        ]
    )

    # 5. NIH ODS Calcium Fact Sheet
    create_pdf(
        "nih_ods_calcium.pdf",
        [
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Calcium",
                """Overview and Mineral Function:
Calcium is the most abundant mineral in the human body. Over 99% of the body's calcium is stored in the bones and teeth, where it supports structure and hardness. The remaining 1% is found in blood, muscle, and intercellular fluids, playing an indispensable role in vascular contraction, vasodilation, muscle function, nerve transmission, and hormonal secretion.

Recommended Dietary Allowances (RDA) for Calcium:
- Children 1-3 years: 700 mg/day
- Children 4-8 years: 1,000 mg/day
- Adolescents 9-18 years: 1,300 mg/day
- Adults 19-50 years: 1,000 mg/day
- Men 51-70 years: 1,000 mg/day
- Women 51-70 years: 1,200 mg/day
- Adults 71+ years: 1,200 mg/day

Tolerable Upper Intake Levels (UL) for Calcium:
- Children 1-8 years: 2,500 mg/day
- Children 9-18 years: 3,000 mg/day
- Adults 19-50 years: 2,500 mg/day
- Adults 51+ years: 2,000 mg/day"""
            ),
            (
                "National Institutes of Health (NIH) - Office of Dietary Supplements | Calcium",
                """Dietary Sources of Calcium:
Dairy products represent the richest and most bioavailable sources of calcium:
- Milk, yogurt, and cheese (approx. 200-300 mg per serving).
- Fortified Foods: Calcium-fortified orange juices, fortified plant milks (soy, almond, oat), and fortified breakfast cereals.
- Non-Dairy Foods: Calcium-set tofu, canned sardines and salmon with soft edible bones, and dark leafy greens such as kale, bok choy, and broccoli. (Spinach contains calcium, but bioavailability is low due to oxalates).

Bone Health and Osteoporosis:
Adequate calcium intake throughout life, as part of a well-balanced diet, may reduce the risk of osteoporosis and bone fractures in older age. Adequate vitamin D intake is necessary to ensure efficient intestinal calcium absorption. Excess calcium intake (primarily from supplements) may increase the risk of nephrolithiasis (kidney stones)."""
            ),
        ]
    )

    # 6. CDC Diabetes Basics & Prevention
    create_pdf(
        "cdc_diabetes_basics.pdf",
        [
            (
                "Centers for Disease Control and Prevention (CDC) | Diabetes Basics and Diagnosis",
                """Overview of Diabetes Mellitus:
Diabetes is a chronic metabolic condition that affects how the body turns food into energy. When blood sugar levels rise, the pancreas normally produces insulin to allow blood glucose into cells for use as energy. In diabetes, the body either does not make enough insulin or cannot use its own insulin effectively.

Primary Classifications:
1. Type 1 Diabetes: An autoimmune reaction where the body's immune system attacks insulin-producing beta cells in the pancreas. Requires daily exogenous insulin administration.
2. Type 2 Diabetes: The body cells become resistant to insulin, and the pancreas cannot produce enough insulin to overcome this resistance. Develops over years and is often preventable.
3. Gestational Diabetes: Develops during pregnancy in females who did not previously have diabetes.

Clinical Diagnostic Criteria:
- Fasting Plasma Glucose (FPG):
  * Normal: Below 100 mg/dL
  * Prediabetes: 100 mg/dL to 125 mg/dL
  * Diabetes: 126 mg/dL or higher on two separate tests
- Hemoglobin A1C (Average Blood Sugar over 3 Months):
  * Normal: Below 5.7%
  * Prediabetes: 5.7% to 6.4%
  * Diabetes: 6.5% or higher on two separate tests"""
            ),
            (
                "Centers for Disease Control and Prevention (CDC) | Diabetes Prevention",
                """Prediabetes and Prevention Strategies:
Prediabetes is a serious health condition where blood sugar levels are higher than normal, but not yet high enough to be diagnosed as type 2 diabetes. Approximately 96 million American adults - more than 1 in 3 - have prediabetes, and over 80% do not know they have it.

CDC National Diabetes Prevention Program (National DPP):
Clinical trials demonstrate that people with prediabetes can cut their risk of developing type 2 diabetes by 58% (71% for adults aged 60 and older) by making modest lifestyle changes:
- Weight Reduction: Losing 5% to 7% of starting body weight (about 10 to 14 pounds for a 200-pound person).
- Physical Activity: Engaging in at least 150 minutes per week of brisk walking or comparable moderate physical activity.
- Healthy Nutrition: Adopting a diet rich in non-starchy vegetables, lean proteins, whole grains, and water instead of sugar-sweetened beverages.

Modifiable Risk Factors for Type 2 Diabetes:
- Overweight or obesity
- Being physically active less than 3 times a week
- High intake of ultra-processed carbohydrates and sugary drinks
- History of gestational diabetes or polycystic ovary syndrome (PCOS)"""
            ),
        ]
    )

    # 7. CDC Physical Activity Guidelines
    create_pdf(
        "cdc_physical_activity.pdf",
        [
            (
                "Centers for Disease Control and Prevention (CDC) | Physical Activity Guidelines",
                """Physical Activity Guidelines for Americans:
Regular physical activity is one of the most important actions people can take to improve their overall health. The CDC and U.S. Department of Health and Human Services recommend distinct weekly targets for aerobic and muscle-strengthening activities for adults.

Adult Aerobic Activity Target (Ages 18-64):
For substantial health benefits, adults should achieve one of the following benchmarks:
- Option 1 (Moderate Intensity): At least 150 minutes (2 hours and 30 minutes) to 300 minutes of moderate-intensity physical activity per week. Examples include brisk walking (at least 2.5 to 3.0 mph), leisure cycling, water aerobics, and active gardening.
- Option 2 (Vigorous Intensity): At least 75 minutes (1 hour and 15 minutes) to 150 minutes of vigorous-intensity physical activity per week. Examples include running, jogging, swimming laps, singles tennis, and fast cycling.
- Option 3: An equivalent combination of moderate and vigorous aerobic activity.
Spread activity throughout the week rather than concentrating it into a single day."""
            ),
            (
                "Centers for Disease Control and Prevention (CDC) | Physical Activity Guidelines",
                """Muscle-Strengthening and Sedentary Behavior:
In addition to aerobic activity, adults should also participate in:
- Muscle-Strengthening Activities: Involving all major muscle groups (legs, hips, back, abdomen, chest, shoulders, and arms) on 2 or more days per week. Examples include lifting weights, working with resistance bands, bodyweight exercises (push-ups, sit-ups, squats), and heavy yard work.
- Reducing Sedentary Time: Adults should move more and sit less throughout the day. Some physical activity is better than none.

Demonstrated Health Benefits:
Immediate Benefits (Single Session):
- Improves sleep quality and reduces daytime fatigue
- Reduces acute anxiety symptoms
- Improves insulin sensitivity and transiently lowers blood pressure

Long-Term Benefits:
- Significantly lowers risk of cardiovascular disease, stroke, hypertension, and type 2 diabetes
- Reduces risk of 8 types of cancer (bladder, breast, colon, endometrium, esophagus, kidney, lung, stomach)
- Enhances bone mineral density and physical functional capacity
- Decreases risk of fall-related injuries in older adults"""
            ),
        ]
    )

    # 8. CDC Cardiovascular Health & Heart Disease
    create_pdf(
        "cdc_cardiovascular_health.pdf",
        [
            (
                "Centers for Disease Control and Prevention (CDC) | Cardiovascular Health",
                """Heart Disease Overview and Statistics:
Heart disease is the leading cause of death for men, women, and people of most racial and ethnic groups in the United States. Coronary artery disease (CAD) is the most common form of heart disease, responsible for the vast majority of myocardial infarctions (heart attacks). CAD occurs when the arteries that supply blood to heart muscle become hardened and narrowed due to plaque buildup.

Major Modifiable Risk Factors:
Three key risk factors are widespread in the general population:
1. High Blood Pressure (Hypertension): Damaging and weakening vascular endothelial lining.
2. High Blood Cholesterol (Elevated LDL): Providing the raw lipid substrate that forms atherosclerotic plaques.
3. Tobacco Smoking: Damaging blood vessels, accelerating plaque formation, and decreasing arterial oxygen levels.
Other contributing health conditions include type 2 diabetes, obesity, physical inactivity, and diets high in saturated fats, trans fats, and sodium."""
            ),
            (
                "Centers for Disease Control and Prevention (CDC) | Cardiovascular Health",
                """Recognizing Heart Attack Symptoms:
A heart attack (myocardial infarction) occurs when blood flow to a section of the heart muscle is abruptly blocked. Common symptoms include:
- Chest Discomfort: Uncomfortable pressure, squeezing, fullness, or center chest pain lasting more than a few minutes.
- Radiating Discomfort: Pain or aching in one or both arms, the back, neck, jaw, or upper stomach.
- Shortness of Breath: With or without chest discomfort.
- Other Signs: Cold sweats, nausea, lightheadedness, or sudden unexplained fatigue.
*Emergency Action*: Call 911 immediately if heart attack symptoms occur.

Evidence-Based Prevention:
- Choose heart-healthy nutrition: Prioritize fresh produce, whole grains, and lean proteins while minimizing sodium and saturated fats.
- Maintain a healthy body weight and target a normal BMI.
- Engage in regular physical activity (minimum 150 min/week).
- Quit smoking and avoid exposure to secondhand smoke.
- Schedule routine preventive screenings for blood pressure, blood glucose, and lipid profiles."""
            ),
        ]
    )

    # 9. MedlinePlus Atherosclerosis
    create_pdf(
        "medlineplus_atherosclerosis.pdf",
        [
            (
                "MedlinePlus / National Library of Medicine | Atherosclerosis",
                """What is Atherosclerosis:
Atherosclerosis is a disease in which plaque builds up inside your arteries. Arteries are blood vessels that carry oxygen-rich blood to your heart and other parts of your body. Plaque is made up of fat, cholesterol, calcium, and other substances found in the blood. Over time, plaque hardens and narrows your arteries, limiting the flow of oxygen-rich blood to your organs and tissues.

Etiology and Vascular Progression:
Atherosclerosis begins when the inner lining of an artery (the endothelium) becomes damaged. Common causes of endothelial damage include:
- High blood levels of low-density lipoprotein (LDL) cholesterol
- Elevated systemic blood pressure
- Chemical toxins from tobacco smoke
- Insulin resistance and uncontrolled diabetes
- Chronic systemic inflammation
Once damage occurs, platelets, cholesterol, and inflammatory cells adhere to the vessel wall, gradually creating a fibrous atherosclerotic plaque."""
            ),
            (
                "MedlinePlus / National Library of Medicine | Atherosclerosis",
                """Associated Clinical Conditions:
Atherosclerosis can affect any artery in the body, leading to different clinical diseases:
- Coronary Artery Disease (CAD): When plaque narrows the coronary arteries supplying the heart muscle, leading to angina (chest pain) or heart attack.
- Carotid Artery Disease: When plaque builds up in arteries on the side of the neck supplying the brain, leading to stroke or transient ischemic attack (TIA).
- Peripheral Artery Disease (PAD): Plaque in arteries supplying blood to the limbs (typically the legs), causing claudication, pain, and tissue loss.
- Chronic Kidney Disease: Caused by narrowing of the renal arteries.

Diagnostic Testing and Clinical Management:
Diagnosis involves physical exams, blood lipid testing, echocardiograms, CT coronary angiograms, and stress testing. Management focuses on lifestyle modifications: adopting a Mediterranean or DASH dietary pattern, regular physical exercise, weight optimization, smoking cessation, and targeted medical management under a physician's care."""
            ),
        ]
    )

    # 10. USDA / HHS Dietary Guidelines for Americans
    create_pdf(
        "usda_dietary_guidelines.pdf",
        [
            (
                "U.S. Department of Agriculture (USDA) & HHS | Dietary Guidelines for Americans",
                """Core Elements of a Healthy Dietary Pattern:
The Dietary Guidelines for Americans emphasizes meeting nutritional needs primarily from nutrient-dense foods and beverages across four core life stages:
1. Vegetables of all types: Dark green, red and orange, legumes (beans, peas, lentils), starchy vegetables, and other vegetables.
2. Fruits: Especially whole fruits (fresh, frozen, canned, or dried without added sugars).
3. Grains: At least half of total grain intake should be 100% whole grains (such as whole wheat bread, oats, brown rice, and quinoa).
4. Dairy and Fortified Alternatives: Fat-free and low-fat (1%) milk, yogurt, cheese, and fortified soy beverages.
5. Protein Foods: Lean meats, poultry, eggs, seafood (targeting 8 ounces per week for adults), beans, peas, lentils, nuts, seeds, and soy products.
6. Oils: Plant oils (canola, corn, olive, soybean, sunflower) and natural oils in seafood and nuts."""
            ),
            (
                "U.S. Department of Agriculture (USDA) & HHS | Dietary Guidelines for Americans",
                """Quantitative Daily Dietary Limits:
To prevent chronic non-communicable diseases, the Guidelines establish specific numeric limits on components of public health concern:

1. Added Sugars:
   - Less than 10 percent of total calories per day starting at age 2.
   - Avoid foods and beverages with added sugars for infants and toddlers under age 2.
   - Major sources include sugar-sweetened beverages, baked goods, and dairy desserts.

2. Saturated Fats:
   - Less than 10 percent of total calories per day starting at age 2.
   - Replace saturated fats (butter, lard, palm oil, coconut oil) with unsaturated fats.

3. Sodium:
   - Less than 2,300 milligrams (mg) per day for adults and adolescents aged 14+.
   - Even lower limits apply to younger children (1,200 mg for ages 1-3; 1,500 mg for 4-8; 1,800 mg for 9-13).

4. Alcoholic Beverages:
   - Adults of legal drinking age can choose not to drink or limit intake to 2 drinks or less per day for men, or 1 drink or less per day for women."""
            ),
        ]
    )

    # 11. WHO Healthy Diet Fact Sheet
    create_pdf(
        "who_healthy_diet.pdf",
        [
            (
                "World Health Organization (WHO) | Healthy Diet Fact Sheet",
                """Global Dietary Principles for Adults:
A healthy diet helps protect against malnutrition in all its forms, as well as non-communicable diseases (NCDs), including heart disease, stroke, type 2 diabetes, and cancer. The World Health Organization (WHO) defines the nutritional foundation of a healthy adult diet:

Key Macronutrient Distributions:
- Fat Intake: Total fat intake should not exceed 30% of total daily energy intake to avoid unhealthy weight gain.
  * Unsaturated fats (found in fish, avocado, nuts, and sunflower, soybean, canola, and olive oils) are preferable to saturated fats.
  * Saturated fats (found in fatty meat, butter, palm and coconut oil, cream, and cheese) should be reduced to less than 10% of total energy.
  * Trans-fats of all kinds should be eliminated, with industrially produced trans-fats banned globally.
- Free Sugars Intake: Free sugars should be reduced to less than 10% of total energy intake. A further reduction to less than 5% (approx. 25 g or 6 teaspoons per day) provides additional health benefits."""
            ),
            (
                "World Health Organization (WHO) | Healthy Diet Fact Sheet",
                """Salt, Sodium, and Potassium Recommendations:
- Sodium and Salt Limits:
  * Adults should consume less than 5 grams of salt per day (equivalent to less than 2 grams of sodium per day).
  * Consuming less than 5 g of salt daily helps prevent hypertension and reduces the risk of stroke and coronary heart disease in the adult population.
  * All salt consumed should be iodized (fortified with iodine), which is essential for healthy fetal brain development and cognitive function.
- Potassium:
  * Adequate potassium intake (at least 3,510 mg per day for adults) through consumption of fresh fruits and vegetables blunts the negative pressor effect of sodium on blood pressure.

Produce and Dietary Fiber Goals:
- Consume at least 400 grams (approx. 5 portions) of fruits and vegetables daily, excluding potatoes, sweet potatoes, and other starchy roots.
- Ensure high intake of whole grains and dietary fiber (at least 25 grams of dietary fiber daily for adults)."""
            ),
        ]
    )


if __name__ == "__main__":
    generate_all()
    print("Corpus generation complete!")

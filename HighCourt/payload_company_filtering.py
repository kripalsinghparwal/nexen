################### Code to separate company payloads and non company payloads ###########################################

import os
import json
import pandas as pd

# Base input and output root directories
base_input_dir = r'D:\Nexensus_Projects\HighCourt\High_court_data\Hightcourt_payload'
base_entity_output_dir = r'D:\Nexensus_Projects\HighCourt\High_court_data\Highcourt_company_payload'
base_non_entity_output_dir = r'D:\Nexensus_Projects\HighCourt\High_court_data\Highcourt_noncompany_payload'

# Entity matching keywords
keywords = ['llp', 'ltd', 'bank', 'limited']

def contains_entity_keyword(name):
    if pd.isna(name):
        return False
    name = name.lower()
    return any(keyword in name for keyword in keywords)

# Loop through all years and categories dynamically
for year in os.listdir(base_input_dir):
    year_path = os.path.join(base_input_dir, year)
    if not os.path.isdir(year_path):
        continue

    for category in os.listdir(year_path):
        category_path = os.path.join(year_path, category)
        if not os.path.isdir(category_path):
            continue

        print(f"\n📁 Processing: Year = {year}, Category = {category}")

        # Define dynamic output directories
        entity_output_dir = os.path.join(base_entity_output_dir, year, category)
        non_entity_output_dir = os.path.join(base_non_entity_output_dir, year, category)
        os.makedirs(entity_output_dir, exist_ok=True)
        os.makedirs(non_entity_output_dir, exist_ok=True)

        for filename in os.listdir(category_path):
            if filename.endswith('.txt'):
                input_path = os.path.join(category_path, filename)
                with open(input_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                data = []
                for line in lines:
                    line = line.strip().rstrip(',')
                    if line:
                        try:
                            obj = json.loads(line)
                            data.append(obj)
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Skipping invalid JSON in {filename}: {e}")

                if not data:
                    continue

                df = pd.DataFrame(data)
                df['isPetitionerEntity'] = df['petitionerName'].apply(contains_entity_keyword)
                df['isRespondentEntity'] = df['respondentName'].apply(contains_entity_keyword)

                non_entities = df[(df['isPetitionerEntity'] == False) & (df['isRespondentEntity'] == False)]
                entities = df[~((df['isPetitionerEntity'] == False) & (df['isRespondentEntity'] == False))]

                # Output file paths
                entity_path = os.path.join(entity_output_dir, filename)
                non_entity_path = os.path.join(non_entity_output_dir, filename)

                with open(non_entity_path, 'w', encoding='utf-8') as f1:
                    for record in non_entities.drop(columns=['isPetitionerEntity', 'isRespondentEntity']).to_dict(orient='records'):
                        f1.write(json.dumps(record) + '\n')

                with open(entity_path, 'w', encoding='utf-8') as f2:
                    for record in entities.drop(columns=['isPetitionerEntity', 'isRespondentEntity']).to_dict(orient='records'):
                        f2.write(json.dumps(record) + '\n')

                print(f"✅ Processed: {filename}")

print("\n🎉 All dynamic folders processed successfully.")

''' This script is used to split csv files for training and testing :
1. Takes the final CSV file
2. Splits it into 70-30 split
3. Save the file as train.csv
4. Split the reamining 30% data based on job roles
5. Save it for unseen data - model evaluation'''

import pandas as pd
from sklearn.model_selection import train_test_split

file_path = "ML_Model/Files/FINAL_DATA_ALL.csv"
df = pd.read_csv(file_path)

train_data, remaining_data = train_test_split(df, test_size=0.3, random_state=42)
train_data.to_csv("ML_Model/Files/train_data.csv", index=False)

job_roles = ["Data Science", "Web Developer", "Java Developer"]
for role in job_roles:
    role_data = remaining_data[remaining_data["job role"] == role]
    role_data.to_csv(f"ML_Model/Files/{role.replace(' ', '_').lower()}_data.csv", index=False)

print("Data split and saved successfully.")
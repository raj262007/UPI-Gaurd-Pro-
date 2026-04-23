

import pandas as pd
import numpy as np
import random

# Seed set karo taaki results reproducible hon
np.random.seed(42)
random.seed(42)

def generate_dataset(n_samples=5000):
    """
    Realistic UPI transaction dataset banata hai.
    
    Fraud patterns jo hum simulate kar rahe hain:
    1. Bahut bada amount raat ko
    2. Naya location se bada transaction
    3. Ek din mein bahut saare transactions
    """
    
    data = []
    
    for i in range(n_samples):
        # Pehle decide karo fraud hoga ya nahi (15% fraud rate realistic hai)
        is_fraud = 1 if random.random() < 0.15 else 0
        
        if is_fraud:
            # FRAUD transaction ka pattern:
            amount = random.choice([
                random.uniform(5000, 50000),   # Bada amount
                random.uniform(100, 500),       # Chhota amount (phishing test)
            ])
            hour = random.choice([0, 1, 2, 3, 22, 23])  # Raat ka time
            location_code = random.choice([1, 2])         # Alag location
            device_type = random.randint(0, 2)
            transaction_type = random.choice([1, 2])      # Transfer ya withdrawal
            prev_txn_count = random.randint(8, 20)        # Bahut saare transactions
        else:
            # SAFE transaction ka pattern:
            amount = random.uniform(10, 4999)    # Normal amount
            hour = random.randint(8, 21)          # Daytime
            location_code = random.choice([0, 0, 0, 1])  # Mostly same location
            device_type = random.choice([0, 0, 1])        # Mostly mobile
            transaction_type = random.randint(0, 2)
            prev_txn_count = random.randint(0, 5)         # Normal frequency
        
        data.append({
            'amount': round(amount, 2),
            'hour': hour,
            'location_code': location_code,
            'device_type': device_type,
            'transaction_type': transaction_type,
            'prev_txn_count': prev_txn_count,
            'fraud': is_fraud
        })
    
    df = pd.DataFrame(data)
    df.to_csv('dataset.csv', index=False)
    
    print("✅ Dataset generated successfully!")
    print(f"   Total records: {len(df)}")
    print(f"   Fraud cases: {df['fraud'].sum()} ({df['fraud'].mean()*100:.1f}%)")
    print(f"   Safe cases: {(df['fraud']==0).sum()}")
    print("\nDataset ka sample:")
    print(df.head())
    print("\nDataset stats:")
    print(df.describe())
    
    return df

if __name__ == "__main__":
    generate_dataset()

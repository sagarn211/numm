import pandas as pd
from app.services.cleaning_service import clean_dataframe
def read_csv_file(path: str):
    return clean_dataframe(pd.read_csv(path))

import pandas as pd
from app.services.cleaning_service import clean_dataframe
def read_excel_file(path: str):
    return clean_dataframe(pd.read_excel(path, engine="openpyxl"))

from pyairtable import Table
from app.config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME

class AirtableService:
    def __init__(self):
        self.table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    
    def get_row_by_app_section(self, app_section):
        records = self.table.all(formula=f"{{App_Section}} = '{app_section}'")
        return records[0]['fields'] if records else None
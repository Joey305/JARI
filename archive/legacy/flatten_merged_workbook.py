
import pandas as pd
import time

def concatenate_excel_sheets_to_csv(source_excel_file, output_csv_file):
    xls = pd.ExcelFile(source_excel_file)
    df_list = []
    start_time = time.time()
    
    # Read the first sheet to set column headers
    first_sheet_df = pd.read_excel(xls, sheet_name=0)
    column_headers = first_sheet_df.columns.tolist()

    for i, sheet_name in enumerate(xls.sheet_names):
        current_time = time.time()
        if current_time - start_time > 30:
            print(f"Still working... Processed {i} sheets so far.")
            start_time = current_time
        
        print(f"Processing sheet {i+1} of {len(xls.sheet_names)}: {sheet_name}")
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # For sheets after the first one, reset column headers to match the first sheet
        if i != 0:  # If not the first sheet
            df.columns = column_headers  # Reset column headers to match the first sheet
            df = df.iloc[1:]  # Skip the header row for subsequent sheets

        df_list.append(df)
    
    # Concatenate all dataframes
    all_data_df = pd.concat(df_list, ignore_index=True)
    
    # Save the concatenated dataframe to a CSV file
    all_data_df.to_csv(output_csv_file, index=False)
    print("Data successfully saved to CSV.")

source_excel_file = 'ALL_NEW_SelfDOCKQ_SCORES.xlsx'
output_csv_file = 'AllDATA_COMBINED.csv'

concatenate_excel_sheets_to_csv(source_excel_file, output_csv_file)

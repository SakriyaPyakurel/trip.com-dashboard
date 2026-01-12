def shuffler(df):
    shuffler = df.sample(frac=1)
    shuffled_df = shuffler.reset_index(drop=True)
    return shuffled_df
def visualize():
    import subprocess 
    try:
        subprocess.run(['python','-m','streamlit','run','dashboard.py'],check=True) 
    except subprocess.CalledProcessError as e: 
        print(f'An error occurred while launching the dashboard: {e}')

def data_extractor():
    try:
        print('Extracting module fully loaded.')
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait 
        from selenium.webdriver.support import expected_conditions as EC
        import pandas as pd
        import time
        import sys
             
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.maximize_window()
        driver.get("https://www.trip.com/flights/")

        if not sys.stdin.isatty():
            scheduler = True
        else:
            scheduler = False  
        if not scheduler:
            input("Select your departure and arrival cities, dates, press search, then press ENTER here...")
        else:
            WebDriverWait(driver,60).until(EC.visibility_of_all_elements_located((By.XPATH,"//div[@data-aria-id='search_city_from0']")))
 
        try:
            dep_city = driver.find_element(By.XPATH, "//div[@data-aria-id='search_city_from0']").text.strip().replace("\n", " ")
        except:
            dep_city = ""
        try:
            arr_city = driver.find_element(By.XPATH, "//div[@data-aria-id='search_city_to0']").text.strip().replace("\n", " ")
        except:
            arr_city = ""

        print(f"Departure: {dep_city}, Arrival: {arr_city}")

        try:
            dep_date = driver.find_element(By.XPATH, "//div[@data-aria-id='search_date_from0']").text.strip()
        except:
            dep_date = ""
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.XPATH,"//div[.//span[contains(text(),'US$') or contains(text(),'$')]]")))
        time.sleep(3)
        flight_blocks = driver.find_elements(By.XPATH, "//div[.//span[contains(text(),'US$') or contains(text(),'$')]]")
        print("Flight cards found:", len(flight_blocks))

        flights = []

        for block in flight_blocks:
            text = block.text.split("\n")
            try:
                price = next((t for t in text if "$" in t), None)
                if not price:
                    continue

                dep_full = ""
                arr_full = ""
                try:
                    time_spans = block.find_elements(
                        By.XPATH,
                        ".//div[contains(@class,'flight-info-airline__timers')]//span[contains(@data-testid,'flight-time')]"
                    )
                    times = []
                    for span in time_spans:
                        dt = span.get_attribute("data-testid")
                        if dt and dt.startswith("flight-time-"):
                            times.append(dt.replace("flight-time-", ""))
                    if len(times) >= 2:
                        dep_full = f"{dep_date} {times[0]}"
                        arr_full = f"{dep_date} {times[1]}"
                except:
                    pass

                airline_candidates = [
                    t for t in text
                    if t not in price and ":" not in t and "$" not in t
                ]
                airline = airline_candidates[0] if airline_candidates else "Unknown"

                flights.append({
                    "From": dep_city,
                    "To": arr_city,
                    "Airline": airline,
                    "Departure Time": dep_full,
                    "Arrival Time": arr_full,
                    "Price(in dollars)": price
                })

            except:
                continue

        df = pd.DataFrame(flights)

        blacklist = [
            "Round-trip", "Recommended", "Alliance", "Stops", "Included",
            "Carry-on", "Unknown", "Search", "Nearby", "Hotels",
            "From", "Nonstop", "Cheapest", "Flights", "One-way",
            "1 stop or fewer", "Oneworld", "SkyTeam", "Star Alliance"
        ]
        pattern = "|".join(blacklist)
        df = df[~df["Airline"].str.contains(pattern, case=False, na=False)]
        df["Airline"] = df["Airline"].str.replace(r"\(\d+\)", "", regex=True).str.strip().str.replace("\n", " ")
        df["From"] = df["From"].str.replace("\n", " ")
        df["To"] = df["To"].str.replace("\n", " ")
        df["Price(in dollars)"] = df["Price(in dollars)"].str.extract(r"(\d+)").astype(int)
        df = df.drop_duplicates().reset_index(drop=True)
        df = df.sort_values(by="Price(in dollars)")
        driver.quit()
        print('Data extraction completed successfully')
        print('Taking care of missing values and invalid formats.....')
        import warnings
        warnings.filterwarnings('ignore')
        df = df[~df['Airline'].str.startswith('1. Departures to')]
        df['Price(in dollars)'] = df['Price(in dollars)'].replace(1, 100)
        df['Departure Time'] = pd.to_datetime(df['Departure Time'], errors='coerce')
        df['Arrival Time'] = pd.to_datetime(df['Arrival Time'], errors='coerce')
        df['Duration'] = df['Arrival Time'] - df['Departure Time']
        mask_next_day = df['Duration'] < pd.Timedelta(0)
        df.loc[mask_next_day, 'Arrival Time'] += pd.Timedelta(days=1)
        df['Duration'] = df['Arrival Time'] - df['Departure Time']  
        median_duration_per_route = (
           df.dropna(subset=['Duration'])
          .groupby(['From', 'To'])['Duration']
          .median()
        )
        mask_arrival = df['Arrival Time'].isna() & df['Departure Time'].notna()
        route_duration = df.loc[mask_arrival].set_index(['From','To']).index.to_series().map(median_duration_per_route)
        df.loc[mask_arrival, 'Arrival Time'] = df.loc[mask_arrival, 'Departure Time'] + route_duration.values
        mask_departure = df['Departure Time'].isna() & df['Arrival Time'].notna()
        route_duration = df.loc[mask_departure].set_index(['From','To']).index.to_series().map(median_duration_per_route)
        df.loc[mask_departure, 'Departure Time'] = df.loc[mask_departure, 'Arrival Time'] - route_duration.values
        mask_both = df['Departure Time'].isna() & df['Arrival Time'].isna()
        if mask_both.any():
            route_min_dep = df.groupby(['From','To'])['Departure Time'].min()
            for idx in df[mask_both].index:
              route = (df.at[idx, 'From'], df.at[idx, 'To'])
              earliest_dep = route_min_dep.get(route, pd.NaT)
              if pd.notna(earliest_dep):
                df.at[idx, 'Departure Time'] = earliest_dep
                df.at[idx, 'Arrival Time'] = earliest_dep + median_duration_per_route.get(route, pd.Timedelta(0))
        df['Duration'] = df['Arrival Time'] - df['Departure Time'] 
        df['Duration_in_hours'] = df['Duration'].dt.total_seconds() / 3600 
        df.drop(df[df['Duration_in_hours']>18].index,inplace=True)
        df.drop(['Duration','Duration_in_hours'],axis=1,inplace=True)
        shuffled_df = shuffler(df) 
        shuffled_df.to_csv('trip_flights_final.csv',mode='a',index=False,header=not pd.io.common.file_exists('trip_flights_final.csv')) 
        # shuffled_df.to_csv('trip_flights_final.csv',index=False,header=True)
        print('Written to csv files successfully')
    except Exception as e:
        print(f'An error occurred: {e}')
if __name__ == "__main__":
    data_extractor()
    visualize()
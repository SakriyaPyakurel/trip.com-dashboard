Due to security advancements(limitations in my case) in trip.com i had to use an advanced python library like selenium instead of basic libraries like requests and bs4(BeautifulSoup) manually checking the html tags and payloads of the webpage itself with automatic iterations for generating adequate quantity of data (Price denoted in american dollars).<br>

# Libraries used:<br>
Selenium : for crossing the security premises of the webpage (authenicity of the data is not guaranteed)<br>
Pandas: for writing the scraped data into csv file after converting it into a dataframe<br>
time: for ensuring breaktime between requests<br>
Streamlit: for interactive dashboards meant for interpretative visualization<br>

# fixes:<br>

-> Shifted from manual iterations to automatic iterations using placeholders and data-aria_id like attributes to extract data<br>
-> Windowtime lasts sufficiently longer than before ensuring the user can input data without worrying about the window getting closed up<br>
-> Streamlit dashboard for Price vs duration scatter plots for stored flights data contained in csv.

# complexities:<br>

->Full formatted Arrival time and departure time couldn't be extracted - the possible reason is frequent change of selected element's attribute and slow response from the fetcher api.
-> Data engineering techniques were applied to fill up none values in Departure and arrival time making the dataset a bit unreal duration wise.
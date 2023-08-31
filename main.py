import re
from tkinter.filedialog import askopenfile
import cv2
from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker
from pytesseract import pytesseract
import time
import googlemaps
import mysql.connector
from datetime import date

Window.size = (300, 550)


def location_data():
    API_KEY = 'AIzaSyAwLcf0HI-Ddu6V3xnqcBkA-b6JOIoGI78'
    gmaps = googlemaps.Client(key=API_KEY)
    places_result = gmaps.places_nearby(location='55.8609825,-4.2488787', radius=40000, open_now=False, type='cafe')
    time.sleep(3)
    gmaps.places_nearby(page_token=places_result['next_page_token'])
    stored_results = []
    while True:
        for place in places_result['results']:
            # define the place id, needed to get place details. Formatted as a string.
            my_place_id = place['place_id']

            # define the fields you would liked return. Formatted as a list.
            my_fields = ['name', 'formatted_address']

            # make a request for the details.
            places_details = gmaps.place(place_id=my_place_id, fields=my_fields)

            # store the results in a list object.
            stored_results.append(places_details['result'])

        if 'next_page_token' not in places_result:
            break  # No more pages to retrieve

        time.sleep(3)  # Wait a bit before making the next request
        places_result = gmaps.places_nearby(page_token=places_result['next_page_token'])
    result_list = []
    for entry in stored_results:
        name = entry['name']
        address = entry['formatted_address']
        result_string = f"{name}, address: \"{address}\""
        result_list.append(result_string)

    return result_list


def cancel(value):
    toast("you click cancel")


class YourApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cnts = None
        self.conts = None
        self.result = None
        self.formatted_strings = None
        self.item = None
        self.path_to_tesseract = None
        self.image_file = None
        self.file = None
        self.menu2 = None
        self.menu1 = None
        self.screens = None
        self.mydb = None
        self.cursor = None
        self.init_database()
        # Initialize any variables or perform setup here

    def init_database(self):
        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="Matcha$1021",
                database="calender_db"
            )
            self.cursor = self.mydb.cursor()
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS coffee_shoo (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        shop_name VARCHAR(255) NOT NULL,
                        coffee_and_price VARCHAR(255) NOT NULL,
                        location VARCHAR(255) NOT NULL,
                        entry_date DATE NOT NULL
                    )
                    """)
            self.mydb.commit()
            return self.mydb
        except mysql.connector.Error as err:
            print(f"Error connecting to the database: {err}")

    def build(self):
        # Build your app's UI here
        self.screens = Builder.load_file('layout.kv')
        coffee_store_data = ["Tim Hortons", "Pret a Manger", "cafe nero", "costa coffee", "black sheep coffee",
                             "starbucks", "others"]

        self.menu1 = MDDropdownMenu(
            caller=self.screens.ids.imagetext4,
            items=self.dropdown(coffee_store_data),
            position="top",
            width_mult=8,
        )
        self.menu2 = MDDropdownMenu(
            caller=self.screens.ids.imagetext5,
            items=self.dropdown(location_data(), loc=True),
            position="bottom",
            width_mult=8,
        )
        self.menu2.menu.max_height = 300
        return self.screens

    def set_item(self, text__item, loc=False):
        if loc:
            self.screens.ids.imagetext5.text = text__item
        if text__item == "others":
            self.screens.ids.imagetext4.text = "."
        elif not loc:
            self.screens.ids.imagetext4.text = text__item
        self.menu1.dismiss()
        self.menu2.dismiss()

    def dropdown(self, data, loc=False):
        menu_item = []
        for item in data:
            if loc:
                akhil = {"text": item, "viewclass": "TwoLineListItem",
                         "on_release": lambda x=item: self.set_item(x, loc=True), }
            else:
                akhil = {"text": item, "viewclass": "OneLineListItem", "on_release": lambda x=item: self.set_item(x), }
            menu_item.append(akhil)
        return menu_item

    extracted_successfully = False

    def filechooser(self):
        try:
            self.file = askopenfile(mode='r', filetypes=[("JPEG files", ".jpeg")])
            self.image_file = self.file.name
        except:
            toast("please select image")

    def extract_image(self):
        self.path_to_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pytesseract.tesseract_cmd = self.path_to_tesseract
        try:
            path_to_image = self.image_file
            img = cv2.imread(path_to_image)  # Read the image

            def grayscale(item):
                return cv2.cvtColor(item, cv2.COLOR_BGR2GRAY)

            gray_image = grayscale(img)
            thresh, im_bw = cv2.threshold(gray_image, 120, 130, cv2.THRESH_BINARY)

            def noise_removal(item):
                import numpy as np
                kernel = np.ones((1, 1), np.uint8)
                item = cv2.dilate(item, kernel, iterations=1)
                kernel = np.ones((1, 1), np.uint8)
                item = cv2.erode(item, kernel, iterations=1)
                item = cv2.morphologyEx(item, cv2.MORPH_CLOSE, kernel)
                item = cv2.medianBlur(item, 3)
                return item

            no_noise = noise_removal(im_bw)

            def thick_font(item):
                import numpy as np
                item = cv2.bitwise_not(item)
                kernel = np.ones((1, 1), np.uint8)
                item = cv2.dilate(item, kernel, iterations=1)
                item = cv2.bitwise_not(item)
                return item

            dilated_image = thick_font(no_noise)
            cv2.imwrite("dilated_image.jpg", dilated_image)
            blur = cv2.GaussianBlur(gray_image, (7, 7), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            self.item = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 13))
            dilate = cv2.dilate(thresh, self.item, iterations=1)
            image = cv2.imread("dilated_image.jpg")
            self.cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.conts = self.cnts[0] if len(self.cnts) == 2 else self.cnts[1]
            for c in self.conts:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
            cv2.imwrite("bbox.jpg", image)
            recognized_text = pytesseract.image_to_string("bbox.jpg")
            recognized_text = recognized_text.split("\n")
            print(recognized_text)
            coffee_data = []
            # Extract coffee names and prices
            for obj in recognized_text:
                coffee_items = re.findall(r'^(\d+)\s?([A-Za-z\s-]+)\s?£([\d.]+)$', obj)
                if coffee_items:
                    coffee_data.append(coffee_items)

            filtered_list = [sublist for sublist in coffee_data if coffee_data]
            print(filtered_list)

            self.formatted_strings = '\n'.join(
                ' '.join(str(element).strip() for element in obj[0]) for obj in filtered_list)
            if self.formatted_strings:
                # Text extraction successful
                self.extracted_successfully = True
            else:
                # Text extraction failed, reset 'formatted_strings'
                self.extracted_successfully = False
                self.formatted_strings = ""
            print(self.formatted_strings)

            self.root.ids.imagetext1.text = self.formatted_strings
        except:
            toast("please select image first")

    def save_buttons(self):
        current_date = date.today()
        if self.extracted_successfully:
            if self.root.ids.imagetext4.text.strip() and self.root.ids.imagetext1.text.strip() \
                    and self.root.ids.imagetext5.text.strip():
                shop_name = self.root.ids.imagetext4.text.strip()
                coffee_and_price = self.formatted_strings
                location = self.root.ids.imagetext5.text.strip()
                self.insert_coffee_shop_data(shop_name, coffee_and_price, location)
                sql = "SELECT shop_name, coffee_and_price, location FROM coffee_shoo WHERE entry_date = %s"
                val = (current_date,)
                self.cursor.execute(sql, val)
                self.result = self.cursor.fetchall()
                self.fetch_data(self.result)
                print(self.result)
            else:
                toast("please enter the required fields before saving.")

        else:
            try:
                if self.root.ids.imagetext4.text.strip() and self.root.ids.imagetext1.text.strip() and \
                        self.root.ids.imagetext5.text.strip():
                    shop_name = self.root.ids.imagetext4.text.strip()
                    coffee_and_price = self.root.ids.imagetext1.text.strip()
                    location = self.root.ids.imagetext5.text.strip()
                    self.insert_coffee_shop_data(shop_name, coffee_and_price, location)
                    sql = "SELECT shop_name, coffee_and_price, location FROM coffee_shoo WHERE entry_date = %s"
                    val = (current_date,)
                    self.cursor.execute(sql, val)
                    self.result = self.cursor.fetchall()
                    self.fetch_data(self.result)
                    print(self.result)
                    # self.root.ids.my_label.text = result
                else:
                    toast("Please Enter the data before saving")
            except:
                print("error occurred")

    def insert_coffee_shop_data(self, shop_name, coffee_and_price, location):
        try:
            # Get the current date
            current_date = date.today()

            # Check if the record with the same unique identifier already exists
            sql = "SELECT id FROM coffee_shoo WHERE shop_name = %s AND coffee_and_price = %s AND location = %s AND " \
                  "entry_date = %s"
            val = (shop_name, coffee_and_price, location, current_date)
            self.cursor.execute(sql, val)
            existing_record = self.cursor.fetchone()

            if existing_record:
                toast("Record already exists.please enter correct data.")
                return
            # Insert data into the table along with the current date
            sql = "INSERT INTO coffee_shoo (shop_name, coffee_and_price, location, entry_date) VALUES (%s, %s, %s, %s)"
            val = (shop_name, coffee_and_price, location, current_date)
            self.cursor.execute(sql, val)

            # Commit the changes to the database
            self.mydb.commit()

            print("Coffee shop data inserted successfully.")
        except Exception as e:
            print(f"Error occurred: {str(e)}")

    def fetch_data(self, data_list, history=False):
        data_text = ''
        for entry in data_list:
            shop_name, coffee_and_price, location = entry
            data_text += f"Shop Name: {shop_name}\n"
            data_text += f"Coffee and Price: {coffee_and_price}\n"
            data_text += f"Location: {location}\n"
            data_text += "--------------------\n"

        # Set the formatted data to the MDLabel
        if history:
            self.root.ids.date_label.text = data_text
        else:
            self.root.ids.my_label.text = data_text

    def date_storer(self):
        date_storer = MDDatePicker()
        date_storer.bind(on_save=self.save, on_cancel=cancel)
        date_storer.open()

    def save(self, instance, value, date_range):
        selected_date = value
        current_date = date.today()
        try:
            sql = "SELECT shop_name, coffee_and_price, location FROM coffee_shoo WHERE entry_date BETWEEN %s AND %s"
            val = (selected_date, current_date)
            self.cursor.execute(sql, val)
            result = self.cursor.fetchall()
            self.fetch_data(result, history=True)
            print(result)
        except:
            toast("no data to be shown")

    menu = None  # Initialize the menu


if __name__ == '__main__':
    YourApp().run()

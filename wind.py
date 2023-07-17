import requests,time, pickle, os
from dotenv import load_dotenv
load_dotenv()
togive = True
key = os.getenv('KEY')
if(not key):
    print("Please set your API key in a .env file. Refer to the README for more information.")
    togive = False
def get(lat, lon):
        response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}")
        d = response.json()
        if d['cod'] == 200:
            return (d['wind']['speed']*1.94384, d['wind']['deg'])
while togive:
        try:
            with open("give.bat","rb") as f:
                pass
        except FileNotFoundError:
            with open('take.bat', 'wb') as f:
                pickle.dump((0,0), f)
        else:
            with open('give.bat', 'rb') as f:
                p = pickle.load(f)
                print(p)
            if p:
                wind = get(*p)
                print(wind)
                if wind:
                    with open('take.bat', 'wb') as f:
                        pickle.dump(wind, f)
        time.sleep(10)
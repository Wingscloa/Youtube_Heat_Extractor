from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pytube import YouTube
import ffmpeg
import subprocess    
import shutil
import os
import re
import argparse


# install requirements.txt


class extractor:

    def __init__(self, url = None,clip = 20, title = None) -> None:
        self.url = input("url : ") if url is None else url
        self.title = None
        self.video_dur = 193
        self.svg = ""
        self.clip = int(clip)
        self.x_high = None
        self.y_high = None
        self.title = title

    def GetSVG(self) -> str:
        # nastavení prohlížeče
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service,options=options)

        try :
            # načtení stranky
            timeout = 10
            driver.get(self.url)
            # WebDriver funguje dokud nejsou načtený všechny nebo timeout neni prerusen
            # elementy a existuje třída {ytp-heat-map-path}
            WebDriverWait(driver,timeout).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ytp-heat-map-path")))
            # Získání HTML obsahu
            page_source = driver.page_source
            # Inicializace BSka, pro parsování html souboru
            soup = BeautifulSoup(page_source,'html.parser')
            # Nacházení ytp-heat-map-path
            div = soup.find('path',class_='ytp-heat-map-path').attrs['d']
            # celkovej cas videa
            time = soup.find('span',class_='ytp-time-duration').text
            minute, second = map(float,time.split(":"))
            self.video_dur = minute * 60 + second
            print(self.video_dur)
        except:
            driver.quit()
            os.system("cls")
            print("The video doesn't have the heatmap or the timeout has expired")
            os._exit(0)
        finally:
            driver.quit()
        return div
    
    def HighestPoint(self,svg : str):
        svg = svg.split()
        body = []

        for points in svg:
            if points.startswith(('M','C')):
                continue
            else:
                x,y = map(float,points.split(','))
                body.append((x,y))

        highests = (0,100)

        for y in body:
            if y[1] < (highests)[1]:
                highests = y

        self.x_high = highests[0]
        self.y_high = highests[1]

        return highests
    
    def HeatTime(self) -> int:
        if self.x_high is not None:
            percent = round(self.x_high/1000,2)
            video_time = self.video_dur * percent
            return int(video_time)
        else:
            print("X and Y are None")

    def HeatTimeStart(self) -> int:
        if self.x_high is not None:
            percent = round(self.x_high/1000,2)
            video_time = self.video_dur * percent
            calc = video_time - (self.clip/2)
            if calc < 0:
                return 0 
            else:
                return calc
        else:
            print("X and Y are None")

    
    def HeatTimeEnd(self) -> int:
        if self.x_high is not None:
            percent = round(self.x_high/1000,2)
            video_time = self.video_dur * percent
            calc = video_time + (self.clip/2)
            if calc > self.video_dur:
                return self.video_dur
            else:
                return calc
        else:
            print("X and Y are None")

    def DownloadHeat(self,outputvideo = "output"):
        ytb_vid = YouTube(self.url)
        ext = outputvideo + ".mp4"

        try:
            self.title = ytb_vid.title if self.title is None else self.title

            video_download = ytb_vid.streams.get_by_itag(ytb_vid.streams.filter(res="1080p")[0].itag).download(filename="video.mp4")
            audio_download = ytb_vid.streams.get_audio_only().download(filename="audio.mp4")
        except:
            print("Error - chyba ve stahování")


        if(shutil.which("ffmpeg") is not None):
            subprocess.run(f"ffmpeg -i video.mp4 -i audio.mp4 -c copy {"1"+ext}",shell=True)
            subprocess.run(f"ffmpeg -i {"1"+ext} -ss {self.HeatTimeStart()} -to {self.HeatTimeEnd()} -c copy {f'"{self.title}.mp4"'}")
        else:
            print("ffmpeg.ouput method")
            video_stream = ffmpeg.input("video.mp4")
            audio_stream = ffmpeg.input("audio.mp4")
            ffmpeg.output(video_stream, audio_stream, "1"+ext).run() 
            ffmpeg.input("1"+ext,ss=self.HeatTimeStart,to=self.HeatTimeEnd).output(ext).run()
        


def is_valid_url(url):
    # Simple regex to validate URL
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def main():
    if not os.path.exists("heat_clip"):
        os.mkdir("heat_clip")
        
    parser =  argparse.ArgumentParser(description="Zpracování atributů z příkazového řádku")
    parser.add_argument("--url", type=str, required=False, help="Enter youtube url of the video")
    parser.add_argument("--clip", type=int, required=False, help="Seconds of the final heat clip")
    parser.add_argument("--name", type=str, required=False, help="Name of the final heat clip")

    args = parser.parse_args()
    url = args.url
    clip = args.clip
    name = args.name

  
    if args.url is None:
        # Pretty print
        print("*******************************")
        print("**    URL Link Requester     **")
        print("*******************************")
        
        url = input("Please enter a valid URL: ").strip()

        if not is_valid_url(url):
            print("Invalid URL. Please try again.")
            os._exit(0)

        os.system("cls")

    if args.clip is None:
        print("*******************************")
        print("**  HOW MANY SECONDS TO CLIP  **")
        print("*******************************")
        
        clip = int(input("Please enter a seconds for clip : ").strip())

        while type(clip) is not int:
            print("Invalid Input. Please try it again")
            clip = int(input("Please enter a seconds for clip : ").strip())
            os.system("cls")

    if args.name is None:
        custom_bool = int(input("Do you want a custom name of output?\n0 - no\n1 - yes\nanswer : "))

        while custom_bool < 0 and 1 < custom_bool and type(custom_bool) is not int:
            print("Write correct answer")
            print("0 - no\n1 - yes")
            custom_bool = input("Do you want a custom name of output?\n0 - no\n1 - yes\nanswer : ")

        name = None
        if custom_bool == 1:
            name = input("Please enter a name for heat clip : ")
            while len(name) < 5 and len(name != 0):
                print("Needs to be 5 letters long. Please try it again")
                name = input("Please enter a name for heat clip : ")
                os.system("cls")
    
    
    try:
        print("STATE : Extracting URL")
        ext = extractor(url,clip=clip,title=name)
        print("STATE : Getting SVG")
        svg = ext.GetSVG()
        print("STATE : Calculating Points")
        ext.HighestPoint(svg)
        print("STATE : Downloading Heat Clip")
        ext.DownloadHeat()

        # mazani zbytecnych slozek
        os.remove("1output.mp4")
        os.remove("audio.mp4")
        os.remove("video.mp4")
        # presunuti slozky


        print(f"{ext.title}")
        os.rename(f"{ext.title}.mp4",f"heat_clip/{ext.title}.mp4")
    except:
        print(f"There's an error, closing a application")
        os._exit(0)

if __name__ == "__main__":
    main()


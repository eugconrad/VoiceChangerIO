import os
import re
import sys
import base64
import random

from datetime import datetime

from typing import Optional, Union, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.remote.webelement import WebElement


class VoiceEffect:
    id: int
    title: str
    element: WebElement

    def __init__(self, id: int, title: str, element: WebElement):
        self.id = id
        self.title = title
        self.element = element


class VoiceChangerIO:
    driver: ChromeWebDriver
    target_site: str
    voice_effects: List[VoiceEffect]

    def __init__(self, driver_options: Optional[Union[list, str]] = None):
        self.driver = self.create_webdriver(options=driver_options)
        self.target_site = "https://voicechanger.io/"
        self.driver.get(self.target_site)
        self.voice_effects = self.get_voice_effects()

    def create_webdriver(self, options: Optional[Union[list, str]] = None) -> ChromeWebDriver:
        chrome_options = ChromeOptions()
        if options is not None:
            if isinstance(options, str):
                chrome_options.add_argument(options)
            elif isinstance(options, list):
                [chrome_options.add_argument(option) for option in options]
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver

    def get_file_content_chrome(self, uri) -> bytes:
        result = self.driver.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
        if type(result) == int:
            raise Exception("Request failed with status %s" % result)
        return base64.b64decode(result)

    def get_voice_effects(self) -> list:
        voice_effects_element = self.driver.find_elements(By.XPATH, "/html/body/section[4]/div/*")
        voice_effects = []
        for i, element in enumerate(voice_effects_element):
            if element.tag_name == "div":
                try:
                    title_element = element.find_element(By.TAG_NAME, "h2")
                    title = title_element.get_attribute("textContent")
                    if title == "":
                        pattern = r"loadTransform\(event, '(.+?)'\)"
                        match = re.search(pattern, element.get_attribute("onclick"))
                        if match:
                            result = match.group(1)
                            title = result.capitalize()
                    voice_effect = VoiceEffect(i, title, element)
                    voice_effects.append(voice_effect)
                except NoSuchElementException:
                    pass
        return voice_effects

    def upload_audio(self, audio_file: Union[bytes, str]) -> True:
        file_input = self.driver.find_element(By.XPATH, "/html/body/section[3]/div[1]/div[1]/input")
        if isinstance(audio_file, bytes):
            audio_file = self.save_audio_file(audio_file)
        file_input.send_keys(audio_file)
        audio_load_card = self.driver.find_element(By.XPATH, "//*[@id=\"audio-load-success\"]")
        audio_load_card_display = audio_load_card.value_of_css_property("display")
        while audio_load_card_display == "none":
            audio_load_card_display = audio_load_card.value_of_css_property("display")
        return True

    def get_output_audio_src(self) -> str:
        audio_element = self.driver.find_element(By.XPATH, "//*[@id=\"output-audio-tag\"]")
        audio_src = audio_element.get_attribute("src")
        while audio_src is None or audio_src == "":
            audio_src = audio_element.get_attribute("src")
        return audio_src

    def download_output_audio(self, audio_src: str) -> bytes:
        audio_bytes = self.get_file_content_chrome(audio_src)
        return audio_bytes

    @staticmethod
    def save_audio_file(audio_file: bytes, custom_name: Optional[str] = None) -> str:
        if custom_name and not custom_name.lower().endswith(".mp3"):
            custom_name += ".mp3"
        file_path = os.path.abspath(custom_name if custom_name else "VoiceChangerIO.mp3")
        with open(file_path, "wb") as binary_file:
            binary_file.write(audio_file)
        return file_path

    def apply_voice_effect(self, audio_file: bytes, voice_effect: VoiceEffect):
        self.upload_audio(audio_file)
        voice_effect.element.click()
        audio_src = self.get_output_audio_src()
        audio_file = self.download_output_audio(audio_src)
        return audio_file


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = end_time.timestamp() - start_time.timestamp()
        print(f"Function '{func.__name__}'")
        print(f"Time start: {start_time}")
        print(f"Time end: {end_time}")
        print(f"Time run: {execution_time:.3}s.")
        return result
    return wrapper


@measure_time
def example() -> int:
    voice_changer_io = VoiceChangerIO(["--headless", "--mute-audio"])
    voice_effect = random.choice(voice_changer_io.voice_effects)
    with open(os.path.abspath("sample.mp3"), "rb") as file:
        file_bytes = file.read()
    audio_file = voice_changer_io.apply_voice_effect(audio_file=file_bytes, voice_effect=voice_effect)
    voice_changer_io.save_audio_file(audio_file, "TEST")
    return 0


if __name__ == "__main__":
    sys.exit(example())
